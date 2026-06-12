import pool from '../config/db.js';

export async function getCategories(req, res) {
  try {
    const [categories] = await pool.query('SELECT * FROM medicine_categories ORDER BY name');
    res.json(categories);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMedicines(req, res) {
  try {
    const { category, search, prescription } = req.query;
    let query = `
      SELECT m.*, c.name AS category_name, c.slug AS category_slug
      FROM medicines m
      JOIN medicine_categories c ON m.category_id = c.id
      WHERE m.is_active = TRUE
    `;
    const params = [];

    if (category) {
      query += ' AND c.slug = ?';
      params.push(category);
    }
    if (search) {
      query += ' AND m.name LIKE ?';
      params.push(`%${search}%`);
    }
    if (prescription === 'false') {
      query += ' AND m.requires_prescription = FALSE';
    }

    query += ' ORDER BY m.name';
    const [medicines] = await pool.query(query, params);
    res.json(medicines);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMedicineById(req, res) {
  try {
    const [medicines] = await pool.query(
      `SELECT m.*, c.name AS category_name
       FROM medicines m
       JOIN medicine_categories c ON m.category_id = c.id
       WHERE m.id = ? AND m.is_active = TRUE`,
      [req.params.id]
    );
    if (medicines.length === 0) {
      return res.status(404).json({ error: 'Medicine not found' });
    }
    res.json(medicines[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createOrder(req, res) {
  try {
    const { items, shipping_address, phone, notes } = req.body;

    if (!items?.length || !shipping_address || !phone) {
      return res.status(400).json({ error: 'Items, shipping address, and phone are required' });
    }

    const connection = await pool.getConnection();
    try {
      await connection.beginTransaction();

      let total = 0;
      const orderItems = [];

      for (const item of items) {
        const [meds] = await connection.query(
          'SELECT * FROM medicines WHERE id = ? AND is_active = TRUE',
          [item.medicine_id]
        );
        if (meds.length === 0) {
          throw new Error(`Medicine ID ${item.medicine_id} not found`);
        }
        const med = meds[0];
        if (med.stock < item.quantity) {
          throw new Error(`Insufficient stock for ${med.name}`);
        }
        const price = med.discounted_price || med.price;
        total += price * item.quantity;
        orderItems.push({ medicine_id: med.id, quantity: item.quantity, price });
      }

      const [orderResult] = await connection.query(
        'INSERT INTO orders (user_id, total_amount, shipping_address, phone, notes) VALUES (?, ?, ?, ?, ?)',
        [req.user.id, total, shipping_address, phone, notes || null]
      );

      for (const item of orderItems) {
        await connection.query(
          'INSERT INTO order_items (order_id, medicine_id, quantity, price) VALUES (?, ?, ?, ?)',
          [orderResult.insertId, item.medicine_id, item.quantity, item.price]
        );
        await connection.query(
          'UPDATE medicines SET stock = stock - ? WHERE id = ?',
          [item.quantity, item.medicine_id]
        );
      }

      await connection.commit();
      res.status(201).json({
        message: 'Order created. Please complete payment.',
        order_id: orderResult.insertId,
        total,
        payment_required: true,
      });
    } catch (err) {
      await connection.rollback();
      throw err;
    } finally {
      connection.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMyOrders(req, res) {
  try {
    const [orders] = await pool.query(
      'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
      [req.user.id]
    );

    for (const order of orders) {
      const [items] = await pool.query(
        `SELECT oi.*, m.name AS medicine_name
         FROM order_items oi
         JOIN medicines m ON oi.medicine_id = m.id
         WHERE oi.order_id = ?`,
        [order.id]
      );
      order.items = items;
    }

    res.json(orders);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
