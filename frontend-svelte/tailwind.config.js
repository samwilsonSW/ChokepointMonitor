/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,svelte}',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@skeletonlabs/skeleton/tailwind/skeleton.cjs')({
      themes: {
        preset: [
          { name: "skeleton", enhancements: true },
          { name: "modern", enhancements: true },
          { name: "vintage", enhancements: true },
          { name: "rocket", enhancements: true },
          { name: "sahara", enhancements: true },
          { name: "hamlindigo", enhancements: true },
          { name: "gold-nouveau", enhancements: true },
          { name: "crimson", enhancements: true }
        ]
      }
    })
  ]
}
