import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  serverExternalPackages: [
    '@google-cloud/documentai',
    '@grpc/grpc-js',
    '@grpc/proto-loader',
    'google-auth-library',
    'google-gax',
  ],
};

export default nextConfig;
