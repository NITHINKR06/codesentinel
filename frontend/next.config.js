/** @type {import('next').NextConfig} */
const nextConfig = {
	eslint: {
		// ESLint is still available via `next lint`, but it won't
		// run (or fail) during `next build`, avoiding the circular
		// config error from the auto-generated .eslintrc.
		ignoreDuringBuilds: true,
	},
}

module.exports = nextConfig