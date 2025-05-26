const webpack = require("webpack");

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // 添加 fallback 配置
      webpackConfig.resolve.fallback = {
        ...webpackConfig.resolve.fallback,
        crypto: require.resolve("crypto-browserify"),
        stream: require.resolve("stream-browserify"),
        buffer: require.resolve("buffer"),
        path: require.resolve("path-browserify"),
        os: require.resolve("os-browserify/browser"),
        constants: require.resolve("constants-browserify"),
        process: require.resolve("process/browser"),
        fs: false,
        readline: false,
        util: require.resolve("util"),
      };

      // 添加别名来解决process/browser模块解析问题
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        "process/browser": require.resolve("process/browser"),
      };

      // 添加 plugins
      webpackConfig.plugins = (webpackConfig.plugins || []).concat([
        new webpack.ProvidePlugin({
          Buffer: ["buffer", "Buffer"],
          process: "process/browser",
        }),
      ]);

      return webpackConfig;
    },
  },
};
