// Vercel serverless: Health check and status
module.exports = (req, res) => {
  const status = {
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    platform: 'vercel',
    version: '1.0.0'
  };
  
  res.status(200).json(status);
};
