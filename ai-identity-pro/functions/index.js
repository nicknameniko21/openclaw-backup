const functions = require('firebase-functions/v2');
const express = require('express');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const app = express();
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || functions.params.JWT_SECRET.default;

// In-memory storage (use Firestore in production)
const users = {};
const twins = {};

// Auth middleware
const verifyToken = (req, res, next) => {
  const auth = req.headers.authorization;
  if (!auth) return res.status(401).json({ error: 'No token' });
  try {
    const token = auth.replace('Bearer ', '');
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
};

// Routes
app.get('/', (req, res) => {
  res.json({ name: 'AI Identity Pro API', version: '2.0.0', status: 'operational' });
});

app.post('/auth/register', (req, res) => {
  const { email, password, name } = req.body;
  const id = crypto.randomUUID();
  users[id] = { id, email, name, tier: 'free', password: crypto.createHash('sha256').update(password).digest('hex') };
  res.json({ user_id: id, token: jwt.sign({ user_id: id }, JWT_SECRET), tier: 'free' });
});

app.post('/auth/login', (req, res) => {
  const { email, password } = req.body;
  const user = Object.values(users).find(u => u.email === email);
  if (!user || user.password !== crypto.createHash('sha256').update(password).digest('hex')) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  res.json({ user_id: user.id, token: jwt.sign({ user_id: user.id }, JWT_SECRET), tier: user.tier });
});

app.get('/user/me', verifyToken, (req, res) => {
  const user = users[req.user.user_id];
  if (!user) return res.status(404).json({ error: 'Not found' });
  res.json({ id: user.id, email: user.email, name: user.name, tier: user.tier });
});

app.post('/twins', verifyToken, (req, res) => {
  const id = crypto.randomUUID();
  twins[id] = { ...req.body, id, user_id: req.user.user_id, created_at: new Date().toISOString() };
  res.json({ twin_id: id, status: 'created' });
});

app.get('/twins', verifyToken, (req, res) => {
  const userTwins = Object.values(twins).filter(t => t.user_id === req.user.user_id);
  res.json({ twins: userTwins });
});

// Export as Firebase Function
exports.api = functions.https.onRequest(app);
