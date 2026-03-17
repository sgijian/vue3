from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存模拟任务数据
mock_tasks = {}
mock_results = {}
mock_dashboard = {}

@app.get("/api/templates")
def get_templates():
    return {
        "job_description": "高级后端开发工程师，5 年以上相关经验，熟悉 Python/Java，具备大型系统设计能力。",
        "evaluation_criteria": "相关经验 30 分，技能深度 30 分，项目成果 20 分，学历 10 分，稳定性 10 分"
    }

@app.post("/api/tasks")
def create_task(data: dict):
    task_id = str(uuid.uuid4())
    # 初始化任务状态为 pending，稍后在轮询中模拟变化
    mock_tasks[task_id] = {
        "status": "pending", 
        "job_description": data.get("job_description"), 
        "evaluation_criteria": data.get("evaluation_criteria"),
        "created_at": time.time()
    }
    
    # 预生成结果和 dashboard 数据，确保字段完整
    mock_results[task_id] = {
        "task_id": task_id,
        "status": "completed",
        "total_candidates": 8,
        "top_3": [
            {"filename": "张三.docx", "profile": {"name": "张三", "relevant_years": 6, "education": {"degree": "硕士", "school": "清华大学"}, "skill_matrix": [{"Python": 5, "Java": 4}], "expected_salary": "30-40K/月"}, "evaluation": {"score": 92, "strength": "架构能力强", "risk": "跳槽频繁", "final_rank": 1}},
            {"filename": "李四.docx", "profile": {"name": "李四", "relevant_years": 7, "education": {"degree": "本科", "school": "北大"}, "skill_matrix": [{"Python": 4, "Java": 5}], "expected_salary": "28-38K/月"}, "evaluation": {"score": 88, "strength": "项目经验丰富", "risk": "沟通需提升", "final_rank": 2}},
            {"filename": "王五.docx", "profile": {"name": "王五", "relevant_years": 5, "education": {"degree": "本科", "school": "复旦大学"}, "skill_matrix": [{"Python": 4, "Java": 4}], "expected_salary": "25-35K/月"}, "evaluation": {"score": 85, "strength": "执行力强", "risk": "管理经验不足", "final_rank": 3}}
        ],
        "all_candidates": [
            {"filename": f"候选人{i+1}.docx", "profile": {"name": f"候选人{i+1}", "relevant_years": 3+i, "education": {"degree": "本科", "school": "XX 大学"}, "skill_matrix": [{"Python": 3+i%3, "Java": 2+i%4}], "expected_salary": f"{20+i}K/月"}, "evaluation": {"score": 60+5*i, "strength": "技能扎实", "risk": "", "final_rank": i+1}} for i in range(8)
        ],
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "created_at": "2026-03-17T10:00:00Z",
        "completed_at": "2026-03-17T10:01:00Z"
    }
    
    mock_dashboard[task_id] = {
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "skill_radar": [
            {"name": "张三", "Python": 5, "Java": 4, "System Design": 5, "Communication": 4}, 
            {"name": "李四", "Python": 4, "Java": 5, "System Design": 4, "Communication": 5}, 
            {"name": "王五", "Python": 4, "Java": 4, "System Design": 3, "Communication": 4}
        ],
        "level_pie": {"专家": 2, "熟练": 4, "了解": 2}
    }
    
    return {"task_id": task_id}

@app.post("/api/tasks/{task_id}/upload")
def upload_resumes(task_id: str, files: list[UploadFile] = File(...)):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
        
    # 校验数量
    if len(files) > 20:
        return JSONResponse(status_code=400, content={"message": "最多只能上传 20 份简历"})
    
    # 校验格式：支持 .doc 和 .docx
    allowed_extensions = ['.doc', '.docx']
    for f in files:
        if not any(f.filename.lower().endswith(ext) for ext in allowed_extensions):
            return JSONResponse(status_code=400, content={"message": f"仅支持 {', '.join(allowed_extensions)} 格式，当前文件：{f.filename}"})
    
    # 模拟上传成功后进入处理流程
    mock_tasks[task_id]["status"] = "processing"
    mock_tasks[task_id]["upload_count"] = len(files)
    
    return {"message": "上传成功", "count": len(files)}

@app.get("/api/tasks/{task_id}/result")
def get_result(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
    
    # 如果任务未完成，返回空或提示
    if mock_tasks[task_id].get("status") != "completed":
        return {"task_id": task_id, "status": "processing", "message": "分析尚未完成"}
        
    return mock_results.get(task_id, {})

@app.get("/api/tasks/{task_id}/dashboard")
def get_dashboard(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
        
    if mock_tasks[task_id].get("status") != "completed":
        return {"task_id": task_id, "status": "processing", "message": "数据尚未生成"}

    return mock_dashboard.get(task_id, {})

@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
    
    task = mock_tasks[task_id]
    status = task.get("status", "pending")
    
    # 模拟状态流转逻辑，用于前端进度条展示
    # 假设：pending -> processing (extracting -> evaluating -> ranking) -> completed
    progress_data = {"total": 100, "current": 0, "stage": "pending", "percentage": 0}
    
    if status == "pending":
        progress_data = {"total": 100, "current": 10, "stage": "extracting", "percentage": 10}
    elif status == "processing":
        # 简单模拟：根据上传后的时间推移改变阶段（实际项目中应由后台真实任务驱动）
        # 这里为了演示前端轮询效果，固定返回一个中间状态，或者可以根据 upload_count 存在与否判断
        if task.get("upload_count"):
             progress_data = {"total": 100, "current": 60, "stage": "evaluating", "percentage": 60}
        else:
             progress_data = {"total": 100, "current": 30, "stage": "extracting", "percentage": 30}
    elif status == "completed":
        progress_data = {"total": 100, "current": 100, "stage": "completed", "percentage": 100}
    
    return {
        "task_id": task_id, 
        "status": status, 
        "progress": progress_data, 
        "created_at": task.get("created_at", "")
    }

# 辅助接口：用于手动触发任务完成（可选，方便测试）
@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str):
    if task_id in mock_tasks:
        mock_tasks[task_id]["status"] = "completed"
        return {"message": "任务已标记为完成"}
    return JSONResponse(status_code=404, content={"message": "任务不存在"})