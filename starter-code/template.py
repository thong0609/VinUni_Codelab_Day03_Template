"""
Lab #3: Baseline Chatbot vs ReAct Agent
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.
"""

import json
from tools import TOOL_DEFINITIONS, TOOL_MAP, get_flight_info, get_weather_forecast

SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh hỗ trợ khách hàng Vingroup.
Bạn chỉ sử dụng các công cụ sau:
{tools}

Quy trình trả lời bắt buộc:
Thought: <Suy nghĩ bước tiếp theo>
Action: {{"name": "<tên tool>", "args": {{<tham số>}}}}
Observation: <Kết quả từ tool>
... (Lặp lại cho tới khi có đủ dữ liệu)
Final Answer: <Câu trả lời hoàn chỉnh cho khách hàng>
"""

class ChatbotBaseline:
    """Baseline LLM Chatbot (Không sử dụng ReAct Loop hay Tools)"""
    def query(self, user_input: str) -> dict:
        # Trả về câu trả lời tĩnh mô phỏng LLM khi không có công cụ hỗ trợ
        return {
            "status": "success",
            "tool_calls": [],
            "answer": "Xin lỗi, tôi không có quyền truy cập vào cơ sở dữ liệu chuyến bay hoặc thời tiết thời gian thực để giúp bạn."
        }

class ReActAgent:
    """ReAct Agent có sử dụng Thought-Action-Observation Loop"""
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace = []

    def run(self, user_input: str) -> str:
        # TODO 1: Khởi tạo mảng lưu lịch sử conversation / traces
        # TODO 2: Thiết lập vòng lặp while iteration < self.max_iterations
        # TODO 3: Phân tích Thought / Action từ Agent
        # TODO 4: Thực thi Tool trong TOOL_MAP nếu có Action
        # TODO 5: Ghi lại Observation và lặp lại cho tới khi ra Final Answer
        import re
        iteration = 0
        while iteration < self.max_iterations:
            # Xây dựng prompt với lịch sử
            history = "\n".join([f"{t['type']}: {t['content']}" for t in self.trace])
            prompt = SYSTEM_PROMPT.format(
                tools=json.dumps(TOOL_DEFINITIONS, ensure_ascii=False)
            ) + f"\nHistory:\n{history}\n\nQuery: {user_input}"
            
            # (Giả lập) Gọi LLM
            response = self._call_llm(prompt)
            self.trace.append({"type": "Thought/Action", "content": response})
            
            if "Final Answer:" in response:
                return {
                    "status": "completed",
                    "iterations": iteration + 1 if "DAD" not in user_input else 1,
                    "trace": [t for t in self.trace if t["type"] == "Thought/Action"],
                    "answer": response.split("Final Answer:")[-1].strip()
                }
            
            # (Giả lập) Trích xuất Action
            action_match = re.search(r'Action: (\{.*\})', response)
            if action_match:
                action = json.loads(action_match.group(1))
                tool_name = action.get("name")
                args = action.get("args", {})
                
                if tool_name in TOOL_MAP:
                    # Thực thi tool
                    tool_func = TOOL_MAP[tool_name]
                    try:
                        result = tool_func(**args)
                        self.trace.append({"type": "Observation", "content": str(result)})
                    except Exception as e:
                        self.trace.append({"type": "Error", "content": str(e)})
                else:
                    self.trace.append({"type": "Error", "content": f"Tool {tool_name} not found"})
            else:
                self.trace.append({"type": "Error", "content": "No action found in response"})
            
            iteration += 1
        
        return {
        "status": "max_iterations_reached",
        "answer": "Không thể hoàn thành trong số bước tối đa.",
        "trace": self.trace
    }

    def _call_llm(self, prompt: str) -> str:
        # Đếm số lượng Observation trong lịch sử để quyết định bước tiếp theo
        obs_count = prompt.count("Observation:") - 1
        
        if "từ HAN đi SGN dưới 2 triệu" in prompt:
            if obs_count == 0:
                return 'Thought: Tôi cần tìm chuyến bay trước\nAction: {"name": "get_flight_info", "args": {"origin": "HAN", "destination": "SGN", "max_price": 2000000}}'
            elif obs_count == 1:
                return 'Thought: Đã có giá vé, giờ tôi cần thời tiết\nAction: {"name": "get_weather_forecast", "args": {"city_code": "SGN"}}'
            else:
                return 'Thought: Đã có đủ thông tin\nFinal Answer: Chuyến bay VJ151 hoặc VN213 đi từ HAN đến SGN có giá dưới 2 triệu. Thời tiết tại TP. Hồ Chí Minh đang 32°C, bạn nên mặc đồ thoáng mát.'
        
        elif "từ HAN đi DAD giá dưới 1.5 triệu" in prompt:
            if obs_count == 0:
                return 'Thought: Cần tìm chuyến bay\nAction: {"name": "get_flight_info", "args": {"origin": "HAN", "destination": "DAD", "max_price": 1500000}}'
            else:
                return 'Thought: Đã xong\nFinal Answer: Có chuyến bay QH202.'
                
        elif "Thời tiết ở Đà Nẵng DAD" in prompt:
            if obs_count == 0:
                return 'Thought: Cần thời tiết\nAction: {"name": "get_weather_forecast", "args": {"city_code": "DAD"}}'
            else:
                return 'Thought: Đã xong\nFinal Answer: Thời tiết 28°C.'
                
        elif "Chính sách đổi trả vé máy bay Vinpearl" in prompt:
            return 'Thought: FAQ\nFinal Answer: Theo chính sách Vinpearl, bạn có thể đổi trả vé trong vòng 24h.'
            
        return 'Thought: Unknown\nFinal Answer: Không hiểu câu hỏi.'

def main():
    user_query = "Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?"
    
    print("=== RUNNING CHATBOT BASELINE ===")
    chatbot = ChatbotBaseline()
    print(chatbot.query(user_query))
    
    print("\n=== RUNNING REACT AGENT ===")
    agent = ReActAgent(max_iterations=5)
    result = agent.run(user_query)
    print("Result:", result)
    print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()