import jwt from 'jsonwebtoken';

export function optionalAuthenticate(req, res, next) {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    return next();
  }

  try {
    const token = header.split(' ')[1];
    req.user = jwt.verify(token, process.env.JWT_SECRET);
  } catch {
    // Invalid token — treat as guest for optional routes
  }

  next();
}
