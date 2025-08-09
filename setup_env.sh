#!/bin/bash

# Scholar Assistant环境配置脚本
# 该脚本将配置Python虚拟环境，安装依赖，配置环境变量，并启动服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "It is not recommended to run this script as root."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
    else
        OS=$(uname -s)
    fi
    log_info "Detected OS: $OS"
}

# 安装系统依赖
install_system_deps() {
    log_info "Installing system dependencies..."
    
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y \
            python3-pip \
            python3-dev \
            build-essential \
            redis-server \
            curl \
            wget \
            git
    elif command_exists yum; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            python3 \
            python3-devel \
            redis \
            curl \
            wget \
            git \
            gcc
    else
        log_error "Unsupported package manager. Please install dependencies manually."
        exit 1
    fi
}

# 创建并激活虚拟环境
setup_virtualenv() {
    log_info "Setting up Python virtual environment..."
    
    if [ -d "venv" ]; then
        log_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    log_success "Virtual environment created and activated"
}

# 安装Python依赖
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # 升级pip
    pip install --no-cache-dir --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install --no-cache-dir -r requirements.txt
    else
        log_error "requirements.txt not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    # 检查安装是否成功
    if [ $? -ne 0 ]; then
        log_error "Failed to install Python dependencies"
        exit 1
    fi
    
    log_success "Python dependencies installed successfully"
}

# 配置环境变量
configure_env() {
    log_info "Configuring environment variables..."
    
    # 创建.env文件（如果不存在）
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Created .env file from example"
        else
            log_error ".env.example not found. Cannot create .env file"
            exit 1
    fi
    fi
    
    # 提示用户编辑.env文件
    log_info "Please edit the .env file to add your API keys:"
    echo "SERPAPI_KEY=your_serpapi_key_here"
    echo "DASHSCOPE_API_KEY=your_dashscope_api_key_here"
    echo "REDIS_HOST=localhost"
    echo "REDIS_PORT=6379"
    echo "REDIS_DB=0"
    
    log_warning "Please edit these values with your actual API keys and Redis configuration"
}

# 清理僵尸进程
cleanup_zombies() {
    log_info "Cleaning up zombie processes..."
    # 向init进程发送SIGCHLD信号，让它收割僵尸进程
    kill -SIGCHLD 1 2>/dev/null || true
    sleep 1
}

# 检查Redis服务状态
check_redis() {
    log_info "Checking Redis service status..."
    
    # 检查Redis是否正在运行
    if pgrep -x "redis-server" > /dev/null; then
        log_success "Redis server is already running"
        return 0
    else
        log_warning "Redis server is not running"
        return 1
    fi
}

# 启动Redis服务
start_redis() {
    log_info "Starting Redis server..."
    
    # 尝试启动Redis
    if command_exists redis-server; then
        redis-server --daemonize yes
        if [ $? -eq 0 ]; then
            log_success "Redis server started successfully"
            return 0
        else
            log_error "Failed to start Redis server"
            return 1
        fi
    else
        log_error "redis-server not found. Please ensure Redis is installed correctly"
        return 1
    fi
}

# 启动FastAPI后端
start_backend() {
    log_info "Starting FastAPI backend..."
    
    # 使用nohup在后台运行后端，并设置正确的信号处理
    nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    # 等待后端启动
    sleep 3
    
    # 检查后端是否成功启动
    if ps -p $BACKEND_PID > /dev/null; then
        log_success "FastAPI backend started successfully (PID: $BACKEND_PID)"
        return 0
    else
        log_error "Failed to start FastAPI backend"
        cat backend.log
        return 1
    fi
}

# 启动Gradio前端
start_frontend() {
    log_info "Starting Gradio frontend..."
    
    # 使用nohup在后台运行前端，并设置正确的信号处理
    nohup python frontend/app.py > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    # 等待前端启动
    sleep 3
    
    # 检查前端是否成功启动
    if ps -p $FRONTEND_PID > /dev/null; then
        log_success "Gradio frontend started successfully (PID: $FRONTEND_PID)"
        return 0
    else
        log_error "Failed to start Gradio frontend"
        cat frontend.log
        return 1
    fi
}

# 检查端口是否被占用
check_ports() {
    log_info "Checking port availability..."
    
    # 检查8000端口 (FastAPI)
    if lsof -i :8000 > /dev/null; then
        log_warning "Port 8000 is already in use. Killing process..."
        kill -9 $(lsof -t -i :8000)
    fi
    
    # 检查7860端口 (Gradio)
    if lsof -i :7860 > /dev/null; then
        log_warning "Port 7860 is already in use. Killing process..."
        kill -9 $(lsof -t -i :7860)
    fi
}

# 显示访问信息
display_access_info() {
    echo
    log_success "Scholar Assistant is now running!"
    echo
    echo -e "Access the application:"
    echo -e "1. FastAPI Backend: http://localhost:8000"
    echo -e "2. Gradio Frontend: http://localhost:7860"
    echo
    echo -e "Logs:"
    echo -e "1. Backend: backend.log"
    echo -e "2. Frontend: frontend.log"
    echo
    echo -e "To stop the application: ./setup_env.sh stop"
    echo -e "To restart the application: ./setup_env.sh restart"
}

# 停止服务
stop_services() {
    log_info "Stopping Scholar Assistant services..."
    
    # 停止后端
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm -f backend.pid
        log_success "FastAPI backend stopped"
    fi
    
    # 停止前端
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f frontend.pid
        log_success "Gradio frontend stopped"
    fi
    
    # 停止Redis（如果由脚本启动）
    if [ -f "redis_started_by_script" ]; then
        pkill redis-server
        rm -f redis_started_by_script
        log_success "Redis server stopped"
    fi
    
    # 清理僵尸进程
    cleanup_zombies
    
    log_success "All services stopped"
}

# 检查依赖
check_dependencies() {
    log_info "Checking required dependencies..."
    
    # 检查Python
    if ! command_exists python3; then
        log_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # 检查pip
    if ! command_exists pip; then
        log_error "pip is not installed. Please install pip first."
        exit 1
    fi
    
    # 检查Redis
    if ! command_exists redis-server; then
        log_warning "Redis not found. Please install Redis before proceeding."
        read -p "Attempt to install Redis? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_system_deps
        else
            exit 1
        fi
    fi
    
    # 检查Uvicorn
    if ! pip show uvicorn > /dev/null; then
        log_warning "Uvicorn not found. Installing..."
        pip install uvicorn
    fi
    
    # 检查Gradio
    if ! pip show gradio > /dev/null; then
        log_warning "Gradio not found. Installing..."
        pip install gradio
    fi
    
    log_success "All dependencies are satisfied"
}

# 重启服务
restart_services() {
    stop_services
    start_services
}

# 启动服务
start_services() {
    # 清理僵尸进程
    cleanup_zombies
    
    # 检查Redis
    if ! check_redis; then
        start_redis
        touch redis_started_by_script
    fi
    
    # 启动后端和前端
    start_backend
    start_frontend
    
    display_access_info
}

# 主程序
main() {
    # 检查脚本参数
    if [ "$1" == "stop" ]; then
        stop_services
    elif [ "$1" == "restart" ]; then
        restart_services
    else
        check_root
        detect_os
        check_ports
        check_dependencies
        
        if [ ! -f ".env" ]; then
            install_system_deps
            setup_virtualenv
            install_python_deps
            configure_env
        else
            log_info "Using existing environment"
            source venv/bin/activate
        fi
        
        start_services
    fi
}

# 启用自定义信号处理
trap 'log_info "Operation cancelled by user"; exit 2' INT

# 执行主程序
main "$@"

# 返回成功状态
exit 0
