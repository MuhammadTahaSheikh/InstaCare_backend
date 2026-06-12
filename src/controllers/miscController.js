import pool from '../config/db.js';

export async function getSpecialties(req, res) {
  try {
    const [specialties] = await pool.query('SELECT * FROM specialties ORDER BY name');
    res.json(specialties);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getCities(req, res) {
  try {
    const [cities] = await pool.query('SELECT * FROM cities ORDER BY name');
    res.json(cities);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getDeals(req, res) {
  try {
    const [deals] = await pool.query(
      `SELECT d.*, l.name AS lab_name
       FROM deals d
       LEFT JOIN labs l ON d.lab_id = l.id
       WHERE d.is_active = TRUE
       ORDER BY d.created_at DESC`
    );
    res.json(deals);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getBlogPosts(req, res) {
  try {
    const [posts] = await pool.query(
      'SELECT id, title, slug, excerpt, image_url, author, published_at FROM blog_posts ORDER BY published_at DESC'
    );
    res.json(posts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getBlogPostBySlug(req, res) {
  try {
    const [posts] = await pool.query('SELECT * FROM blog_posts WHERE slug = ?', [req.params.slug]);
    if (posts.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }
    res.json(posts[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
