module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        minecraft: ['"Minecraft"', 'sans-serif'],
      },
      colors: {
        surface: '#1e1e1e',
        accent: '#5b8cff',
      },
      boxShadow: {
        floating: '0 20px 45px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
};
