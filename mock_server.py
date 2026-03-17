from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
import random

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
    # 初始化任务状态为 pending
    mock_tasks[task_id] = {
        "status": "pending", 
        "job_description": data.get("job_description"), 
        "evaluation_criteria": data.get("evaluation_criteria"),
        "created_at": time.time(),
        "files": [] # 用于存储上传的文件名
    }
    
    # 【真实场景提示】：此处不应预生成结果，而应触发异步 Celery/Redis 任务
    # 真实逻辑：await ai_service.analyze(task_id, data)
    
    return {"task_id": task_id}

@app.post("/api/tasks/{task_id}/upload")
def upload_resumes(task_id: str, files: list[UploadFile] = File(...)):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
        
    # 校验数量
    if len(files) > 20:
        return JSONResponse(status_code=400, content={"message": "最多只能上传 20 份简历"})
    
    # 校验格式
    allowed_extensions = ['.doc', '.docx']
    for f in files:
        if not any(f.filename.lower().endswith(ext) for ext in allowed_extensions):
            return JSONResponse(status_code=400, content={"message": f"仅支持 {', '.join(allowed_extensions)} 格式，当前文件：{f.filename}"})
    
    # 记录上传的文件名，用于后续生成动态模拟数据
    uploaded_filenames = [f.filename for f in files if f.filename]
    mock_tasks[task_id]["files"] = uploaded_filenames
    
    # 【关键修改】模拟上传成功后直接进入 completed 状态
    mock_tasks[task_id]["status"] = "completed"
    mock_tasks[task_id]["upload_count"] = len(files)
    
    return {"message": "上传成功", "count": len(files)}

@app.get("/api/tasks/{task_id}/result")
def get_result(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
    
    if mock_tasks[task_id].get("status") != "completed":
        return {"task_id": task_id, "status": "processing", "message": "分析尚未完成"}
    
    # 【真实场景提示】：此处应从数据库查询分析结果
    # 真实逻辑：result = db.query(Result).filter_by(task_id=task_id).first()
    
    # 为了演示效果，根据上传的文件名动态生成部分数据，增加真实感
    uploaded_files = mock_tasks[task_id].get("files", [])
    candidate_count = len(uploaded_files) if uploaded_files else 8
    
    # 如果没有上传文件，使用默认数据；如果有，尝试映射文件名
    names = [f.split('.')[0] for f in uploaded_files] if uploaded_files else ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
    
    all_candidates = []
    for i, name in enumerate(names[:candidate_count]):
        score = random.randint(60, 95)
        all_candidates.append({
            "filename": f"{name}.docx",
            "profile": {
                "name": name,
                "relevant_years": random.randint(1, 10),
                "education": {"degree": random.choice(["本科", "硕士", "博士"]), "school": f"{random.choice(['清华', '北大', '复旦', '交大'])}大学"},
                "skill_matrix": [{"Python": random.randint(3, 5)}, {"Java": random.randint(3, 5)}],
                "expected_salary": f"{random.randint(20, 50)}K/月"
            },
            "evaluation": {
                "score": score,
                "strength": "技能扎实" if score > 80 else "潜力股",
                "risk": "无" if score > 85 else "经验稍浅",
                "final_rank": i + 1
            }
        })
    
    # 排序
    all_candidates.sort(key=lambda x: x["evaluation"]["score"], reverse=True)
    for idx, c in enumerate(all_candidates):
        c["evaluation"]["final_rank"] = idx + 1

    mock_results[task_id] = {
        "task_id": task_id,
        "status": "completed",
        "total_candidates": len(all_candidates),
        "top_3": all_candidates[:3],
        "all_candidates": all_candidates,
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "created_at": "2026-03-17T10:00:00Z",
        "completed_at": "2026-03-17T10:01:00Z"
    }
    
    return mock_results.get(task_id, {})

@app.get("/api/tasks/{task_id}/dashboard")
def get_dashboard(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
        
    if mock_tasks[task_id].get("status") != "completed":
        return {"task_id": task_id, "status": "processing", "message": "数据尚未生成"}

    # 【真实场景提示】：此处应从数据统计服务获取
    # 真实逻辑：stats = analytics_service.get_dashboard_stats(task_id)
    
    # 复用 result 中的数据生成图表数据
    result = mock_results.get(task_id, {})
    candidates = result.get("all_candidates", [])
    
    skill_radar = []
    level_pie = {"专家": 0, "熟练": 0, "了解": 0}
    
    for c in candidates:
        name = c["profile"]["name"]
        score = c["evaluation"]["score"]
        # 模拟雷达图数据
        skill_radar.append({
            "name": name,
            "Python": random.randint(3, 5),
            "Java": random.randint(3, 5),
            "System Design": random.randint(3, 5),
            "Communication": random.randint(3, 5)
        })
        
        # 模拟饼图数据
        if score >= 90:
            level_pie["专家"] += 1
        elif score >= 75:
            level_pie["熟练"] += 1
        else:
            level_pie["了解"] += 1
            
    mock_dashboard[task_id] = {
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "skill_radar": skill_radar,
        "level_pie": {k: v for k, v in level_pie.items() if v > 0} # 移除数量为 0 的项
    }

    return mock_dashboard.get(task_id, {})

@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str):
    if task_id not in mock_tasks:
        return JSONResponse(status_code=404, content={"message": "任务不存在"})
    
    task = mock_tasks[task_id]
    status = task.get("status", "pending")
    
    progress_data = {"total": 100, "current": 0, "stage": "pending", "percentage": 0}
    
    if status == "pending":
        progress_data = {"total": 100, "current": 10, "stage": "extracting", "percentage": 10}
    elif status == "processing":
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

@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str):
    if task_id in mock_tasks:
        mock_tasks[task_id]["status"] = "completed"
        return {"message": "任务已标记为完成"}
    return JSONResponse(status_code=404, content={"message": "任务不存在"})