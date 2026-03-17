from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

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
        "job_description": "高级后端开发工程师，5年以上相关经验，熟悉Python/Java，具备大型系统设计能力。",
        "evaluation_criteria": "相关经验30分，技能深度30分，项目成果20分，学历10分，稳定性10分"
    }

@app.post("/api/tasks")
def create_task(data: dict):
    task_id = str(uuid.uuid4())
    mock_tasks[task_id] = {"status": "pending", "job_description": data.get("job_description"), "evaluation_criteria": data.get("evaluation_criteria")}
    # 预生成结果和dashboard
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
            {"filename": f"候选人{i+1}.docx", "profile": {"name": f"候选人{i+1}", "relevant_years": 3+i, "education": {"degree": "本科", "school": "XX大学"}, "skill_matrix": [{"Python": 3+i%3, "Java": 2+i%4}], "expected_salary": f"{20+i}K/月"}, "evaluation": {"score": 60+5*i, "strength": "技能扎实", "risk": "", "final_rank": i+1}} for i in range(8)
        ],
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "created_at": "2026-03-17T10:00:00Z",
        "completed_at": "2026-03-17T10:01:00Z"
    }
    mock_dashboard[task_id] = {
        "score_distribution": {"average": 78, "max_score": 92, "min_score": 60, "high_count": 2, "medium_count": 5, "low_count": 1},
        "skill_radar": [{"name": "张三", "Python": 5, "Java": 4}, {"name": "李四", "Python": 4, "Java": 5}, {"name": "王五", "Python": 4, "Java": 4}],
        "level_pie": {"专家": 2, "熟练": 4, "了解": 2}
    }
    return {"task_id": task_id}

@app.post("/api/tasks/{task_id}/upload")
def upload_resumes(task_id: str, files: list[UploadFile] = File(...)):
    # 只做格式校验和数量校验
    if len(files) > 20:
        return JSONResponse(status_code=400, content={"message": "最多只能上传20份简历"})
    for f in files:
        if not f.filename.endswith('.docx'):
            return JSONResponse(status_code=400, content={"message": "仅支持.docx格式"})
    mock_tasks[task_id]["status"] = "completed"
    return {"message": "上传成功"}

@app.get("/api/tasks/{task_id}/result")
def get_result(task_id: str):
    return mock_results.get(task_id, {})

@app.get("/api/tasks/{task_id}/dashboard")
def get_dashboard(task_id: str):
    return mock_dashboard.get(task_id, {})

@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str):
    # 简单模拟进度
    status = mock_tasks.get(task_id, {}).get("status", "pending")
    progress = {"total": 8, "current": 8 if status == "completed" else 2, "stage": "ranking" if status == "completed" else "extracting", "percentage": 100 if status == "completed" else 30}
    return {"task_id": task_id, "status": status, "progress": progress, "created_at": "2026-03-17T10:00:00Z"}
