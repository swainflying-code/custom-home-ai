"""
AI服务层
封装MIMO大模型调用，提供统一的AI服务接口
"""

import json
import logging
from typing import Dict, Any, List, Optional
import openai
from functools import wraps

from .config import config
from .cache import cache_result


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class AIService:
    """AI服务类 - 封装所有AI相关操作"""
    
    def __init__(self):
        """初始化AI客户端"""
        try:
            self.client = openai.OpenAI(
                api_key=config.ai.api_key,
                base_url=config.ai.base_url
            )
            self.model = config.ai.model
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"AI服务初始化成功，模型: {self.model}")
        except Exception as e:
            self.logger.error(f"AI服务初始化失败: {e}")
            raise AIServiceError(f"AI服务初始化失败: {e}")
    
    def _safe_json_parse(self, text: str) -> Dict[str, Any]:
        """安全解析JSON响应"""
        try:
            # 清理可能的markdown代码块
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败: {e}")
            return {
                "error": "AI返回数据格式错误",
                "raw_response": text
            }
    
    @cache_result(ttl=3600)  # 缓存1小时
    def analyze_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        客户智能分析
        
        Args:
            customer_data: 客户数据字典
            
        Returns:
            AI分析结果
        """
        try:
            # 构建提示词
            system_prompt = """你是一位融合了全球顶尖大师方法论的全屋定制客户顾问。

基于以下大师的专业体系进行分析：
1. 消费心理学：丹尼尔·卡尼曼行为经济学、马斯洛需求层次理论
2. 营销管理：菲利普·科特勒STP理论、尼尔·雷克汉姆SPIN销售法
3. 设计美学：原研哉无印良品设计哲学、深泽直人无意识设计
4. 成交转化：乔·吉拉德销售法则

请对客户提供深度分析，返回标准JSON格式。"""

            user_prompt = f"""请对以下不锈钢定制客户进行深度分析：

客户信息:
{json.dumps(customer_data, ensure_ascii=False, indent=2)}

请按照以下结构返回分析结果：
{{
  "综合评分": {{
    "总分": 85,
    "评分说明": "分析说明"
  }},
  "客户画像标签": ["标签1", "标签2"],
  "可成交预期": {{
    "预期分数": 78,
    "预期说明": "成交概率分析",
    "建议成交周期": "1周内"
  }},
  "详细分析": {{
    "客户心理画像": {{
      "分析结论": "结论",
      "置信度": "高/中/低",
      "具体建议": ["建议1", "建议2"]
    }},
    "消费决策特征": {{...}},
    "设计需求优先级": {{...}},
    "预算合理性评估": {{...}},
    "潜在增值服务": {{...}},
    "沟通建议策略": {{...}},
    "风险点识别": {{...}},
    "高成交跟进计划": {{...}}
  }}
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=config.ai.max_tokens
            )
            
            analysis_text = response.choices[0].message.content
            
            if not analysis_text:
                raise AIServiceError("AI返回内容为空")
            
            # 尝试解析JSON
            result = self._safe_json_parse(analysis_text)
            
            # 如果不是错误结果，添加成功标记
            if "error" not in result:
                result["_success"] = True
                result["_model"] = self.model
                result["_timestamp"] = json.dumps("current_time")
            
            return result
            
        except openai.AuthenticationError:
            error_msg = "API认证失败，请检查API密钥"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except openai.RateLimitError:
            error_msg = "API请求频率超限，请稍后重试"
            self.logger.warning(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"AI分析失败: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    @cache_result(ttl=7200)  # 缓存2小时
    def generate_design_prompt(self, 
                             customer_data: Dict[str, Any], 
                             design_adjustment: str) -> Dict[str, str]:
        """
        生成设计说明和文生图提示词
        
        Args:
            customer_data: 客户数据
            design_adjustment: 设计师调整说明
            
        Returns:
            包含设计说明和提示词的字典
        """
        try:
            system_prompt = """你是一位融合了原研哉无印良品设计哲学的不锈钢定制设计师。

请基于客户的需求和设计师的调整，生成：
1. 详细的设计方案说明
2. 专业的AI生图提示词（适合Midjourney/DALL-E）

要求：
- 设计说明要包含空间布局、功能设计、材质搭配、色彩方案
- 提示词要包含风格关键词、材质描述、色彩搭配、照明氛围、空间布局、装饰元素、生成参数
- 遵循MUJI极简美学理念"""

            user_prompt = f"""客户背景:
{json.dumps(customer_data, ensure_ascii=False, indent=2)}

设计师调整:
{design_adjustment}

请生成:
1. 设计说明
2. 文生图提示词"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            result = response.choices[0].message.content
            
            if not result:
                raise AIServiceError("生成设计提示词失败")
            
            # 解析结果（分为设计说明和提示词）
            lines = result.split('\n')
            design_suggestions = []
            prompt_keywords = []
            in_prompt_section = False
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['提示词', 'prompt', '生图']):
                    in_prompt_section = True
                    prompt_keywords.append(line)
                elif in_prompt_section:
                    prompt_keywords.append(line)
                else:
                    design_suggestions.append(line)
            
            return {
                "design_suggestion": '\n'.join(design_suggestions).strip(),
                "prompt_keywords": '\n'.join(prompt_keywords).strip(),
                "_success": True
            }
            
        except Exception as e:
            error_msg = f"生成设计提示词失败: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "design_suggestion": "",
                "prompt_keywords": ""
            }
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = None,
                       max_tokens: int = None) -> str:
        """
        通用聊天完成
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            AI回复内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or config.ai.temperature,
                max_tokens=max_tokens or config.ai.max_tokens
            )
            
            result = response.choices[0].message.content
            
            if not result:
                raise AIServiceError("AI返回内容为空")
            
            return result
            
        except Exception as e:
            error_msg = f"AI对话失败: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise AIServiceError(error_msg)


# 全局AI服务实例
ai_service = AIService()
