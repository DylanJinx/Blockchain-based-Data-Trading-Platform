import axios from "axios";

const API_URL = "http://localhost:8765/api";

/**
 * 检查数据集是否存在水印
 * @param {string} metadataUrl 数据集元数据URL
 * @returns {Promise<Object>} 检查结果
 */
const checkDatasetWatermark = async (metadataUrl) => {
  try {
    // 首先从元数据URL获取数据集的CID
    const response = await axios.get(metadataUrl);
    const metadata = response.data;
    const datasetCid = metadata.zip_cid || metadata.cid;

    if (!datasetCid) {
      throw new Error("元数据中未找到数据集CID");
    }

    // 调用后端API检查水印
    const checkResponse = await axios.post(`${API_URL}/check-watermark`, {
      dataset_cid: datasetCid,
      metadata_url: metadataUrl,
    });

    // 确保返回的对象中总是包含 has_watermark 字段
    if (
      checkResponse.data &&
      typeof checkResponse.data.has_watermark === "boolean"
    ) {
      return checkResponse.data;
    } else {
      // 如果API返回的结构不包含预期字段，做一个兼容处理
      console.warn("API返回的数据结构不符合预期:", checkResponse.data);
      return {
        has_watermark: false,
        message: "无法确定水印状态，API返回的数据结构不符合预期",
        raw_data: checkResponse.data,
      };
    }
  } catch (error) {
    console.error("检查水印失败:", error);

    // 特别处理 403 状态码，表示检测到了水印
    if (error.response && error.response.status === 403) {
      return {
        has_watermark: true,
        error:
          error.response.data?.message ||
          error.response.data?.error ||
          "检测到水印，禁止登记",
        status_code: 403,
      };
    }

    return {
      has_watermark: false,
      error: error.message,
      error_occurred: true,
    };
  }
};

const apiService = {
  checkReportStatus: async (token_id_a, token_id_b, user_address) => {
    try {
      const response = await axios.post(`${API_URL}/check-report-status`, {
        token_id_a,
        token_id_b,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("检查举报状态失败:", error);
      throw error;
    }
  },

  getBaseUrl: () => {
    return API_URL;
  },

  // 聊天API
  sendMessage: async (message, address) => {
    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message,
        address,
        user_id: localStorage.getItem("userId") || "anonymous",
      });
      return response.data;
    } catch (error) {
      console.error("发送消息失败:", error);
      throw error;
    }
  },

  // 数据集登记API
  registerData: async (metadata_url, user_address) => {
    try {
      // 先检查数据集是否有水印
      const watermarkCheck = await checkDatasetWatermark(metadata_url);

      if (watermarkCheck.has_watermark) {
        // 如果检测到水印，直接返回错误，不发起登记请求
        console.error("检测到数据集存在水印，禁止登记。");
        return {
          status: "error",
          message:
            "检测到该数据集存在水印！该数据集可能是从其他地方购买并转售的，为保护原创作者权益，禁止登记。",
          has_watermark: true,
        };
      }

      // 检查水印检测是否出现了错误
      if (watermarkCheck.error_occurred) {
        console.warn("水印检测过程中出现错误:", watermarkCheck.error);
      }

      // 如果没有水印，继续登记流程
      const response = await axios.post(`${API_URL}/register-data`, {
        metadata_url,
        user_address,
      });

      // 检查响应中是否有水印相关错误
      if (response.data.has_watermark) {
        return {
          status: "error",
          message:
            response.data.error ||
            response.data.message ||
            "检测到该数据集存在水印，禁止登记。",
          has_watermark: true,
        };
      }

      return response.data;
    } catch (error) {
      console.error("数据集登记失败:", error);

      // 特别处理403错误（水印检测）
      if (error.response && error.response.status === 403) {
        return {
          status: "error",
          message:
            error.response.data.error ||
            error.response.data.message ||
            "检测到该数据集存在水印，禁止登记。",
          has_watermark: true,
        };
      }

      // 包装其他错误，确保前端得到一致的响应格式
      return {
        status: "error",
        message: error.message || "未知错误",
        error: true,
      };
    }
  },

  // 上架NFT API
  listNFT: async (token_id, price, user_address) => {
    try {
      const response = await axios.post(`${API_URL}/list-nft`, {
        token_id,
        price,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("NFT上架失败:", error);
      throw error;
    }
  },

  // 下架NFT API
  unlistNFT: async (token_id, user_address) => {
    try {
      const response = await axios.post(`${API_URL}/unlist-nft`, {
        token_id,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("NFT下架失败:", error);
      throw error;
    }
  },

  // 购买NFT API
  buyNFT: async (token_id, user_address, public_key) => {
    try {
      console.log(`开始购买NFT，token_id=${token_id}, user=${user_address}`);
      console.log(`使用的公钥长度: ${public_key.length} 字符`);

      const response = await axios.post(
        `${API_URL}/buy-nft`,
        {
          token_id,
          user_address,
          public_key,
        },
        {
          // 增加超时时间，因为后端处理可能需要较长时间
          timeout: 300000, // 5分钟超时
        }
      );

      console.log("购买NFT响应:", response.data);
      return response.data;
    } catch (error) {
      console.error("NFT购买失败:", error);
      if (error.response) {
        console.error("错误响应数据:", error.response.data);
        console.error("错误状态:", error.response.status);
      } else if (error.request) {
        console.error("请求已发送但未收到响应");
      } else {
        console.error("请求配置错误:", error.message);
      }
      throw error;
    }
  },

  // 举报NFT API
  reportNFT: async (token_id_a, token_id_b, user_address) => {
    try {
      const response = await axios.post(`${API_URL}/report-nft`, {
        token_id_a,
        token_id_b,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("举报NFT失败:", error);
      throw error;
    }
  },

  // 获取所有上架的NFTs
  getListedNFTs: async () => {
    try {
      const response = await axios.get(`${API_URL}/get-listed-nfts`);
      return response.data;
    } catch (error) {
      console.error("获取NFT列表失败:", error);
      throw error;
    }
  },

  // 获取单个NFT详情
  getNFTDetails: async (token_id) => {
    try {
      const response = await axios.get(`${API_URL}/nft/${token_id}`);
      return response.data;
    } catch (error) {
      console.error("获取NFT详情失败:", error);
      throw error;
    }
  },

  // 上传文件到IPFS
  uploadToIPFS: async (file) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API_URL}/upload-to-ipfs`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      console.error("上传到IPFS失败:", error);
      throw error;
    }
  },

  // 检查注册状态
  checkRegisterStatus: async (metadata_url, user_address) => {
    try {
      console.log(
        `请求检查注册状态: URL=${metadata_url}, 用户=${user_address}`
      );

      const response = await axios.post(
        `${API_URL}/check-register-status`,
        {
          metadata_url,
          user_address,
        },
        {
          // 增加超时时间
          timeout: 30000, // 30秒超时
          // 启用重试
          retry: 3,
          retryDelay: 1000,
        }
      );

      console.log("注册状态API响应:", response.data);

      // 数据验证
      if (response.data.status === "success" && !response.data.token_id) {
        console.warn("API返回success状态但缺少token_id字段:", response.data);
        // 尝试从响应中提取token_id
        let token_id = null;
        try {
          // 尝试从消息中提取token_id
          const match = (response.data.message || "").match(
            /token[_-]?id[=:\s]+(\d+)/i
          );
          if (match) {
            token_id = match[1];
            console.log(`从消息中提取到token_id: ${token_id}`);
          }
        } catch (e) {
          console.error("提取token_id失败:", e);
        }

        // 如果提取到token_id，修复响应
        if (token_id) {
          return {
            ...response.data,
            token_id: token_id,
            fixed_response: true,
          };
        }
      }

      return response.data;
    } catch (error) {
      console.error("检查注册状态失败:", error);

      // 错误处理，返回更友好的错误对象
      if (error.response) {
        // 服务器返回了错误状态码
        return {
          status: "error",
          message:
            error.response.data?.message ||
            error.response.data?.error ||
            `服务器错误 (${error.response.status})`,
          http_status: error.response.status,
        };
      } else if (error.request) {
        // 请求已发送但未收到响应
        return {
          status: "error",
          message: "服务器未响应，请稍后重试",
          error_type: "no_response",
        };
      } else {
        // 请求设置有问题
        return {
          status: "error",
          message: `请求失败: ${error.message}`,
          error_type: "request_error",
        };
      }
    }
  },

  // 检查数据集水印 - 添加到apiService对象
  checkDatasetWatermark,
};

export default apiService;
