<template>
  <header class="hero">
    <div class="hero-inner">
      <div class="hero-badge">AI搜索诊断报告</div>
      <h1 class="hero-title">{{ company }}<br />AI搜索诊断报告</h1>
      <p class="hero-sub">豆包AI · 品牌可见度诊断</p>
    </div>
    <svg class="hero-art" viewBox="0 0 750 340" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="panelA" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#8b5cf6" stop-opacity="0.9" />
          <stop offset="1" stop-color="#4c1d95" stop-opacity="0.4" />
        </linearGradient>
        <linearGradient id="panelB" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#c084fc" stop-opacity="0.7" />
          <stop offset="1" stop-color="#6d28d9" stop-opacity="0.3" />
        </linearGradient>
        <radialGradient id="glow" cx="0.5" cy="0.45" r="0.6">
          <stop offset="0" stop-color="#e9d5ff" stop-opacity="0.55" />
          <stop offset="1" stop-color="#e9d5ff" stop-opacity="0" />
        </radialGradient>
      </defs>
      <rect width="750" height="340" fill="none" />
      <ellipse cx="375" cy="150" rx="330" ry="150" fill="url(#glow)" />
      <g opacity="0.85">
        <polygon points="90,300 150,120 210,120 150,300" fill="url(#panelB)" />
        <polygon points="240,300 300,90 360,90 300,300" fill="url(#panelA)" />
        <polygon points="390,300 450,100 510,100 450,300" fill="url(#panelB)" />
        <polygon points="540,300 600,130 660,130 600,300" fill="url(#panelA)" />
      </g>
      <g font-family="'PingFang SC','Microsoft YaHei',sans-serif" font-weight="700">
        <text x="352" y="205" font-size="86" fill="#f5f0ff" text-anchor="middle" letter-spacing="4">AI</text>
        <circle cx="432" cy="132" r="10" fill="#f0abfc" />
      </g>
      <g stroke="#c4b5fd" stroke-width="1" opacity="0.5">
        <line x1="0" y1="300" x2="750" y2="300" />
        <line x1="150" y1="300" x2="300" y2="90" opacity="0.25" />
        <line x1="450" y1="300" x2="600" y2="130" opacity="0.25" />
      </g>
    </svg>
  </header>
</template>

<script setup>
defineProps({ company: { type: String, default: '' } })
</script>

<style scoped>
.hero {
  position: relative;
  background: linear-gradient(180deg, #2e1065 0%, #4c1d95 55%, #6d28d9 100%);
  overflow: hidden;
  padding: 54px 20px 0;
  min-height: 300px;
}
.hero-inner { position: relative; z-index: 2; text-align: center; }
.hero-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #ede9fe;
  font-size: 13px;
  padding: 6px 18px;
  border-radius: 999px;
  margin-bottom: 18px;
}
.hero-title {
  margin: 0;
  color: #ffffff;
  font-size: 30px;
  line-height: 1.45;
  font-weight: 800;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.35);
}
.hero-sub {
  color: #c4b5fd;
  font-size: 14px;
  margin: 12px 0 0;
  letter-spacing: 2px;
}
.hero-art {
  display: block;
  width: 100%;
  height: 200px;
  margin-top: -30px;
}
</style>
