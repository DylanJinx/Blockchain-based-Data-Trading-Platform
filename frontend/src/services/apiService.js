import axios from "axios";

// 创建带有基本URL和超时设置的axios实例
const api = axios.create({
  baseURL: "http://localhost:8765/api",
  timeout: 30000, // 默认30秒超时
});

// 检查水印的专用实例（更长的超时）
const longTimeoutApi = axios.create({
  baseURL: "http://localhost:8765/api",
  timeout: 180000, // 水印检查使用3分钟超时
});

class ApiService {
  // 检查数据集是否存在水印 (使用长超时)
  async checkDatasetWatermark(metadata_url, dataset_cid) {
    try {
      console.log("开始检查水印，metadata_url:", metadata_url);
      // 使用长超时实例
      const response = await longTimeoutApi.post("/check-watermark", {
        metadata_url,
        dataset_cid,
      });
      console.log("水印检查响应:", response.data);
      return response.data;
    } catch (error) {
      console.error("水印检查失败:", error);

      // 处理不同类型的错误
      if (error.code === "ECONNABORTED") {
        return {
          has_watermark: false,
          error: "请求超时，检查水印操作耗时过长",
          timeout: true,
        };
      }

      // 如果服务器返回了响应
      if (error.response) {
        // 检查是否是超时状态码
        if (error.response.status === 408) {
          return {
            has_watermark: false,
            error: "服务器处理超时，水印检查操作耗时过长",
            timeout: true,
          };
        }
        // 返回服务器提供的错误信息
        return {
          has_watermark: false,
          error: error.response.data.error || "水印检查失败",
          error_occurred: true,
        };
      }

      // 其他网络错误
      return {
        has_watermark: false,
        error: error.message || "网络错误，无法完成水印检查",
        error_occurred: true,
      };
    }
  }

  // 注册数据集
  async registerData(metadata_url, user_address) {
    try {
      console.log("开始注册数据集，用户地址:", user_address);
      const response = await api.post("/register-data", {
        metadata_url,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("数据集注册失败:", error);

      // 处理服务器返回的错误
      if (error.response) {
        // 如果是水印错误 (403)
        if (error.response.status === 403) {
          throw new Error(
            error.response.data.message || "检测到水印，禁止登记"
          );
        }

        // 如果是超时错误 (408)
        if (error.response.status === 408) {
          throw new Error(
            error.response.data.message || "注册超时，请稍后重试"
          );
        }

        // 其他服务器错误
        throw new Error(
          error.response.data.message || error.response.data.error || "注册失败"
        );
      }

      // 如果是客户端超时
      if (error.code === "ECONNABORTED") {
        throw new Error("请求超时，注册操作耗时过长");
      }

      // 其他网络错误
      throw error;
    }
  }

  // 检查注册状态
  async checkRegisterStatus(metadata_url, user_address) {
    try {
      console.log("检查注册状态，用户地址:", user_address);
      const response = await api.post("/check-register-status", {
        metadata_url,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("检查注册状态失败:", error);
      throw error;
    }
  }

  // 列出NFT
  async listNft(token_id, price, user_address) {
    try {
      const response = await api.post("/list-nft", {
        token_id,
        price,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("NFT上架失败:", error);
      throw error;
    }
  }

  // 下架NFT
  async unlistNft(token_id, user_address) {
    try {
      const response = await api.post("/unlist-nft", {
        token_id,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("NFT下架失败:", error);
      throw error;
    }
  }

  // 购买NFT
  async buyNft(token_id, user_address, public_key) {
    try {
      const response = await api.post("/buy-nft", {
        token_id,
        user_address,
        public_key,
      });
      return response.data;
    } catch (error) {
      console.error("NFT购买失败:", error);
      throw error;
    }
  }

  // 举报NFT
  async reportNft(token_id_a, token_id_b, user_address) {
    try {
      const response = await api.post("/report-nft", {
        token_id_a,
        token_id_b,
        user_address,
      });
      return response.data;
    } catch (error) {
      console.error("NFT举报失败:", error);
      throw error;
    }
  }

  // 检查转账状态
  async checkTransfer(from_address, to_address, amount_eth) {
    try {
      const response = await api.post("/check-transfer", {
        from_address,
        to_address,
        amount_eth,
      });
      return response.data;
    } catch (error) {
      console.error("检查转账失败:", error);
      throw error;
    }
  }

  // 聊天接口
  async sendMessage(message, user_id, address) {
    try {
      const response = await api.post("/chat", {
        message,
        user_id,
        address,
      });
      return response.data;
    } catch (error) {
      console.error("发送消息失败:", error);
      throw error;
    }
  }

  // 获取所有上架的NFT
  async getListedNfts() {
    try {
      const response = await api.get("/get-listed-nfts");
      return response.data;
    } catch (error) {
      console.error("获取上架NFT列表失败:", error);
      throw error;
    }
  }

  // 获取NFT详情
  async getNftDetails(token_id) {
    try {
      const response = await api.get(`/nft/${token_id}`);
      return response.data;
    } catch (error) {
      console.error(`获取NFT(ID=${token_id})详情失败:`, error);
      throw error;
    }
  }
}

const apiService = new ApiService();
export default apiService;
