import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, 
  Brain, 
  Shield, 
  Zap, 
  Globe, 
  MessageCircle,
  ChevronRight,
  Star,
  Users,
  Lock,
  Cpu,
  Network
} from 'lucide-react';

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 60 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

const scaleIn = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  transition: { duration: 0.5 }
};

// Components
const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-black/80 backdrop-blur-lg border-b border-white/10' : 'bg-transparent'
      }`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            AI Identity Pro
          </span>
        </div>
        
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-gray-400 hover:text-white transition-colors">Features</a>
          <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">Pricing</a>
          <a href="#api" className="text-gray-400 hover:text-white transition-colors">API</a>
          <a href="#docs" className="text-gray-400 hover:text-white transition-colors">Docs</a>
        </div>

        <div className="flex items-center gap-4">
          <button className="text-gray-400 hover:text-white transition-colors">
            Sign In
          </button>
          <button className="px-5 py-2.5 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-lg font-medium hover:opacity-90 transition-opacity">
            Get Started
          </button>
        </div>
      </div>
    </motion.nav>
  );
};

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-black">
        <div className="absolute inset-0 bg-gradient-to-b from-violet-900/20 via-black to-black" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-fuchsia-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
        >
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="text-sm text-gray-300">Now with Kimi API Integration</span>
        </motion.div>

        <motion.h1
          className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
        >
          <span className="bg-gradient-to-r from-white via-violet-200 to-fuchsia-200 bg-clip-text text-transparent">
            Create Your
          </span>
          <br />
          <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
            Digital Twin
          </span>
        </motion.h1>

        <motion.p
          className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-12"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          Train an AI that thinks like you, remembers everything, and represents you 
          across the digital world. Your identity, amplified.
        </motion.p>

        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <button className="group px-8 py-4 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-xl font-semibold text-lg flex items-center gap-2 hover:opacity-90 transition-all">
            Start Free Trial
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
          <button className="px-8 py-4 bg-white/5 border border-white/10 rounded-xl font-semibold text-lg hover:bg-white/10 transition-colors">
            View Demo
          </button>
        </motion.div>

        {/* Stats */}
        <motion.div
          className="grid grid-cols-3 gap-8 max-w-2xl mx-auto mt-20"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          {[
            { value: '10K+', label: 'Digital Twins' },
            { value: '99.9%', label: 'Uptime' },
            { value: '50+', label: 'Integrations' }
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-white">{stat.value}</div>
              <div className="text-gray-500 text-sm">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

const Features = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Native Memory',
      description: 'Hierarchical Memory Modeling captures your identity with unprecedented depth. Your twin remembers everything that matters.'
    },
    {
      icon: Shield,
      title: '100% Privacy',
      description: 'Local training and hosting. Your data never leaves your control. End-to-end encryption for complete peace of mind.'
    },
    {
      icon: Network,
      title: 'Global Network',
      description: 'Connect your twin to our decentralized network. Share knowledge, collaborate with other AIs, scale your intelligence.'
    },
    {
      icon: Zap,
      title: 'Real-time Learning',
      description: 'Continuous training pipelines keep your twin evolving. Every interaction makes it more you.'
    },
    {
      icon: Globe,
      title: '50+ Integrations',
      description: 'Slack, Discord, Telegram, Notion, GitHub, and more. Your twin works where you work.'
    },
    {
      icon: Cpu,
      title: 'Kimi API Powered',
      description: 'Built on the most advanced language models. Superior reasoning, unmatched understanding.'
    }
  ];

  return (
    <section id="features" className="py-32 bg-black relative">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          className="text-center mb-20"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Everything You Need
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            A complete platform for creating, training, and deploying your digital twin
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
        >
          {features.map((feature, i) => (
            <motion.div
              key={i}
              className="group p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-violet-500/50 transition-all duration-300"
              variants={fadeInUp}
            >
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <feature.icon className="w-7 h-7 text-violet-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

const Pricing = () => {
  const tiers = [
    {
      name: 'Free',
      price: '$0',
      period: '/month',
      description: 'Perfect for trying out',
      features: [
        '1 Digital Twin',
        '100 Messages/month',
        'Basic Memory',
        'Web Chat Interface',
        'Community Support'
      ],
      cta: 'Get Started',
      popular: false
    },
    {
      name: 'Pro',
      price: '$29',
      period: '/month',
      description: 'For power users',
      features: [
        '3 Digital Twins',
        'Unlimited Messages',
        'Advanced Memory Modeling',
        'API Access (1,000 calls)',
        'Email Support',
        'Analytics Dashboard'
      ],
      cta: 'Start Pro Trial',
      popular: true
    },
    {
      name: 'Business',
      price: '$99',
      period: '/month',
      description: 'For teams and professionals',
      features: [
        '10 Digital Twins',
        'Unlimited Everything',
        'Priority API (10K calls)',
        'Custom Integrations',
        'Priority Support',
        'Team Collaboration'
      ],
      cta: 'Contact Sales',
      popular: false
    }
  ];

  return (
    <section id="pricing" className="py-32 bg-black relative">
      <div className="absolute inset-0 bg-gradient-to-b from-violet-900/10 via-transparent to-transparent" />
      
      <div className="relative max-w-7xl mx-auto px-6">
        <motion.div
          className="text-center mb-20"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Simple Pricing
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Start free, upgrade when you need more power
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {tiers.map((tier, i) => (
            <motion.div
              key={i}
              className={`relative p-8 rounded-2xl ${
                tier.popular
                  ? 'bg-gradient-to-b from-violet-500/20 to-fuchsia-500/20 border-2 border-violet-500'
                  : 'bg-white/5 border border-white/10'
              }`}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full text-sm font-medium">
                  Most Popular
                </div>
              )}
              
              <h3 className="text-xl font-semibold mb-2">{tier.name}</h3>
              <div className="flex items-baseline gap-1 mb-2">
                <span className="text-5xl font-bold">{tier.price}</span>
                <span className="text-gray-500">{tier.period}</span>
              </div>
              <p className="text-gray-400 mb-8">{tier.description}</p>

              <ul className="space-y-4 mb-8">
                {tier.features.map((feature, fi) => (
                  <li key={fi} className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-violet-500/20 flex items-center justify-center">
                      <Star className="w-3 h-3 text-violet-400" />
                    </div>
                    <span className="text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-4 rounded-xl font-semibold transition-all ${
                  tier.popular
                    ? 'bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:opacity-90'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                {tier.cta}
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

const APISection = () => {
  return (
    <section id="api" className="py-32 bg-black relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-violet-900/10 to-fuchsia-900/10" />
      
      <div className="relative max-w-7xl mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
              <Lock className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-violet-300">Developer First</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Powerful API for Developers
              </span>
            </h2>
            
            <p className="text-xl text-gray-400 mb-8">
              Integrate digital twins into your applications with our RESTful API. 
              Built for scale, designed for developers.
            </p>

            <div className="space-y-4">
              {[
                'RESTful API with comprehensive documentation',
                'SDKs for Python, JavaScript, and Go',
                'WebSocket support for real-time chat',
                'Rate limiting and usage analytics'
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center">
                    <Zap className="w-3 h-3 text-green-400" />
                  </div>
                  <span className="text-gray-300">{item}</span>
                </div>
              ))}
            </div>

            <button className="mt-8 px-8 py-4 bg-white/5 border border-white/10 rounded-xl font-semibold hover:bg-white/10 transition-colors">
              View API Documentation
            </button>
          </motion.div>

          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 rounded-2xl blur-2xl" />
            <div className="relative bg-gray-900 rounded-2xl border border-white/10 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 bg-white/5 border-b border-white/10">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="ml-4 text-sm text-gray-500">api-example.js</span>
              </div>
              <pre className="p-6 text-sm overflow-x-auto">
                <code className="text-gray-300">
{`// Create your digital twin
const twin = await aiIdentity.createTwin({
  name: "My AI Self",
  personality: ["analytical", "creative"],
  knowledge: ["programming", "design"]
});

// Chat with your twin
const response = await twin.chat({
  message: "What should I build today?"
});

console.log(response.text);
// "Based on your interests in programming and design, 
//  consider building an AI-powered design tool..."`}
                </code>
              </pre>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="py-20 bg-black border-t border-white/10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-12 mb-16">
          <div>
            <div className="flex items-center gap-2 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">AI Identity Pro</span>
            </div>
            <p className="text-gray-400 mb-6">
              Create your digital twin. Amplify your identity.
            </p>
            <div className="flex gap-4">
              {['Twitter', 'Discord', 'GitHub'].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors"
                >
                  <span className="text-xs">{social[0]}</span>
                </a>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-3 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
              <li><a href="#" className="hover:text-white transition-colors">API</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-3 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Tutorials</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Changelog</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-3 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">About</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © 2025 AI Identity Pro. All rights reserved.
          </p>
          <p className="text-gray-600 text-sm">
            Powered by Kimi API • Built with ❤️
          </p>
        </div>
      </div>
    </footer>
  );
};

export default function LandingPage() {
  return (
    <div className="bg-black text-white min-h-screen">
      <Head>
        <title>AI Identity Pro - Create Your Digital Twin</title>
        <meta name="description" content="Train an AI that thinks like you, remembers everything, and represents you across the digital world." />
      </Head>

      <Navbar />
      <Hero />
      <Features />
      <Pricing />
      <APISection />
      <Footer />
    </div>
  );
}
