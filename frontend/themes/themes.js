/** Theme registry. WuWa and NTE keep separate theme lists. */

const WUWA_THEMES = [
  {
    id: "classic",
    name: "Cổ Kính",
    subtitle: "Classic Gold HUD",
    description: "Thanh điều hướng cổ điển, viền kim loại vàng hoàng gia và nền xanh navy huyền bí.",
    tag: "Hoàng Gia",
    accentColor: "#f0d89a",
    palette: ["#f0d89a", "#c9a84c", "#050b18"],
    iconSvg: `<svg class="theme-card-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/></svg>`,
    css: "themes/wuwa-classic/theme.css",
    previewGradient: "linear-gradient(135deg, #241b0b 0%, #3d2e10 50%, #081228 100%)",
  },
  {
    id: "modern",
    name: "Hiện Đại",
    subtitle: "Modern Cyber Dock",
    description: "Thanh dock thu gọn bên trái với menu mở rộng, hiệu ứng kính mờ và màu xanh Mint tương lai.",
    tag: "Tối Giản",
    accentColor: "#2dd4bf",
    palette: ["#2dd4bf", "#0d9488", "#0a161f"],
    iconSvg: `<svg class="theme-card-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L4 9l8 13 8-13-8-7zm0 2.5l5.5 4.8H6.5L12 4.5zM6 10.8h4.5l-3.3 5.4-1.2-5.4zm6.5 6.9l-3.2-5.4h6.4l-3.2 5.4zm2-5.4h4.5l-1.2 5.4-3.3-5.4z"/></svg>`,
    css: "themes/wuwa-modern/theme.css",
    previewGradient: "linear-gradient(135deg, #092625 0%, #0d4a45 50%, #081119 100%)",
  },
  {
    id: "dangdev",
    name: "Huyền Sắc",
    subtitle: "Watercolor Ember",
    description: "Giao diện thủy mặc với sidebar tối, ánh đồng và điểm nhấn đỏ trầm.",
    tag: "Thủy Mặc",
    accentColor: "#e5cd98",
    palette: ["#e5cd98", "#943e2e", "#202021"],
    iconSvg: `<svg class="theme-card-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M12 3c-3 5-7 7-7 12a7 7 0 0 0 14 0c0-5-4-7-7-12Z"/><path d="M9 17c1 1 3 1 4 0"/></svg>`,
    css: "themes/wuwa-dangdev/theme.css",
    previewGradient: "linear-gradient(135deg, #202021 0%, #943e2e 52%, #e5cd98 100%)",
  }
];

const NTE_THEMES = [
  {
    id: "cyber",
    name: "Tương Lai",
    subtitle: "Cyberpunk Crimson HUD",
    description: "Giao diện NTE Hologram tông đỏ Neon, lưới tọa độ và viền góc công nghệ.",
    tag: "Viễn Tưởng",
    accentColor: "#ff1a53",
    palette: ["#ff1a53", "#ff4d6d", "#7b0028"],
    iconSvg: `<svg class="theme-card-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h10M7 12h5M7 17h10"/><circle cx="17" cy="12" r="1.5" fill="currentColor"/></svg>`,
    css: "themes/nte-cyber/theme.css",
    previewGradient: "linear-gradient(135deg, #0d0004 0%, #2e020d 50%, #050002 100%)",
  }
];

const THEMES = WUWA_THEMES;

function getThemesForGame(gameId) {
  return gameId === "nte" ? NTE_THEMES : WUWA_THEMES;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { THEMES, WUWA_THEMES, NTE_THEMES, getThemesForGame };
}
