#!/usr/bin/env python3
"""
ArchieAI Setup Wizard
=====================
Interactive setup wizard for installing and configuring ArchieAI.
Supports both Python and Rust implementations.
"""

import os
import sys
import subprocess
import platform
import shutil
import re
from pathlib import Path


# Constants
AVAILABLE_MODELS = [
    "llama2",
    "llama3",
    "qwen3",
    "mistral",
    "codellama"
]
DEFAULT_MODEL = "llama2"
RUST_IMPLEMENTATION_STATUS = "experimental - not fully implemented"


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_command_exists(command):
    """Check if a command exists in the system PATH"""
    return shutil.which(command) is not None


def run_command(command, shell=False, capture_output=False):
    """Run a shell command and return the result"""
    try:
        if capture_output:
            result = subprocess.run(
                command if isinstance(command, list) or shell else command.split(),
                shell=shell,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        else:
            result = subprocess.run(
                command if isinstance(command, list) or shell else command.split(),
                shell=shell,
                check=True
            )
            return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)


def check_python():
    """Check if Python is installed with correct version"""
    print_info("Checking Python installation...")
    if not check_command_exists("python") and not check_command_exists("python3"):
        print_error("Python is not installed!")
        return False
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} is installed")
        return True
    else:
        print_error(f"Python 3.8+ is required. You have Python {version.major}.{version.minor}.{version.micro}")
        return False


def check_pip():
    """Check if pip is installed"""
    print_info("Checking pip installation...")
    if check_command_exists("pip") or check_command_exists("pip3"):
        print_success("pip is installed")
        return True
    else:
        print_error("pip is not installed!")
        return False


def check_ollama():
    """Check if Ollama is installed"""
    print_info("Checking Ollama installation...")
    if check_command_exists("ollama"):
        print_success("Ollama is installed")
        return True
    else:
        print_warning("Ollama is not installed!")
        print_info("Please install Ollama from: https://ollama.ai/")
        return False


def check_cargo():
    """Check if Cargo (Rust) is installed"""
    print_info("Checking Cargo/Rust installation...")
    if check_command_exists("cargo"):
        print_success("Cargo is installed")
        return True
    else:
        print_warning("Cargo/Rust is not installed!")
        print_info("Please install Rust from: https://rustup.rs/")
        return False


def create_data_directories():
    """Create necessary data directories"""
    print_info("Creating data directories...")
    
    data_dir = Path("data")
    sessions_dir = data_dir / "sessions"
    
    try:
        # Create data directory
        data_dir.mkdir(exist_ok=True)
        print_success(f"Created directory: {data_dir}")
        
        # Create sessions directory
        sessions_dir.mkdir(exist_ok=True)
        print_success(f"Created directory: {sessions_dir}")
        
        # Create qna.json if it doesn't exist
        qna_file = data_dir / "qna.json"
        if not qna_file.exists():
            with open(qna_file, 'w') as f:
                f.write('{}')
            print_success(f"Created file: {qna_file}")
        else:
            print_info(f"File already exists: {qna_file}")
        
        # Create users.json if it doesn't exist
        users_file = data_dir / "users.json"
        if not users_file.exists():
            with open(users_file, 'w') as f:
                f.write('{}')
            print_success(f"Created file: {users_file}")
        else:
            print_info(f"File already exists: {users_file}")
        
        return True
    except Exception as e:
        print_error(f"Failed to create data directories: {e}")
        return False


def setup_env_file():
    """Setup .env file from .env.example"""
    print_info("Setting up .env file...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print_error(".env.example not found!")
        return False
    
    if env_file.exists():
        try:
            response = input(f"{Colors.WARNING}.env file already exists. Overwrite? (y/N): {Colors.ENDC}").strip().lower()
        except EOFError:
            response = 'n'
        if response != 'y':
            print_info("Keeping existing .env file")
            return True
    
    try:
        # Copy .env.example to .env
        shutil.copy(env_example, env_file)
        print_success("Created .env file from .env.example")
        
        # Ask user if they want to configure the model
        try:
            response = input(f"\n{Colors.OKCYAN}Would you like to configure the Ollama model now? (y/N): {Colors.ENDC}").strip().lower()
        except EOFError:
            response = 'n'
        
        if response == 'y':
            print_info("\nAvailable models:")
            for model in AVAILABLE_MODELS:
                if model == DEFAULT_MODEL:
                    print(f"  - {model} (default)")
                elif model == "qwen3":
                    print(f"  - {model} (recommended for tool calling)")
                else:
                    print(f"  - {model}")
            
            try:
                model = input(f"\n{Colors.OKCYAN}Enter model name (press Enter for {DEFAULT_MODEL}): {Colors.ENDC}").strip()
            except EOFError:
                model = ''
            
            if model:
                # Update MODEL in .env file using regex to be more robust
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Use regex to replace MODEL value, ensuring we match the entire line
                content = re.sub(r'^MODEL=.*$', f'MODEL={model}', content, flags=re.MULTILINE)
                
                with open(env_file, 'w') as f:
                    f.write(content)
                
                print_success(f"Model set to: {model}")
        
        return True
    except Exception as e:
        print_error(f"Failed to setup .env file: {e}")
        return False


def install_python_dependencies():
    """Install Python dependencies from requirements.txt"""
    print_info("Installing Python dependencies...")
    
    if not Path("requirements.txt").exists():
        print_error("requirements.txt not found!")
        return False
    
    print_info("This may take a few minutes...")
    
    # Determine pip command
    pip_cmd = "pip3" if check_command_exists("pip3") else "pip"
    
    # Install dependencies - use list for security
    success, output = run_command([pip_cmd, "install", "-r", "requirements.txt"])
    
    if success:
        print_success("Python dependencies installed successfully")
        return True
    else:
        print_error(f"Failed to install Python dependencies: {output}")
        return False


def setup_python():
    """Setup Python implementation"""
    print_header("Python Setup")
    
    # Check prerequisites
    if not check_python():
        return False
    
    if not check_pip():
        return False
    
    ollama_installed = check_ollama()
    
    # Create data directories
    if not create_data_directories():
        return False
    
    # Setup .env file
    if not setup_env_file():
        return False
    
    # Install dependencies
    if not install_python_dependencies():
        return False
    
    print_success("\n✓ Python setup completed successfully!")
    
    if not ollama_installed:
        print_warning("\nNote: Ollama is not installed. Please install it to use ArchieAI.")
        print_info("Visit: https://ollama.ai/")
    
    print_info("\nTo run ArchieAI:")
    print(f"  {Colors.BOLD}python src/app.py{Colors.ENDC}")
    print(f"  Then visit: {Colors.BOLD}http://localhost:5000{Colors.ENDC}")
    
    return True


def setup_rust():
    """Setup Rust implementation"""
    print_header("Rust Setup")
    
    print_warning(f"Note: Rust implementation is {RUST_IMPLEMENTATION_STATUS}!")
    
    # Check prerequisites
    if not check_cargo():
        print_error("Cargo is required for Rust setup")
        return False
    
    ollama_installed = check_ollama()
    
    # Create data directories
    if not create_data_directories():
        return False
    
    # Setup .env file
    if not setup_env_file():
        return False
    
    # Build Rust project
    print_info("Building Rust project...")
    print_info("This may take a few minutes...")
    
    # Use list for security
    success, output = run_command(["cargo", "build", "--release"])
    
    if success:
        print_success("Rust project built successfully")
    else:
        print_error(f"Failed to build Rust project: {output}")
        return False
    
    print_success("\n✓ Rust setup completed successfully!")
    
    if not ollama_installed:
        print_warning("\nNote: Ollama is not installed. Please install it to use ArchieAI.")
        print_info("Visit: https://ollama.ai/")
    
    print_info("\nTo run ArchieAI:")
    print(f"  {Colors.BOLD}cargo run --release{Colors.ENDC}")
    
    return True


def main():
    """Main setup wizard"""
    print_header("ArchieAI Setup Wizard")
    
    print(f"{Colors.BOLD}Welcome to ArchieAI Setup!{Colors.ENDC}\n")
    print("This wizard will help you install and configure ArchieAI.\n")
    
    # Choose implementation
    print(f"{Colors.OKCYAN}Choose implementation:{Colors.ENDC}")
    print("  1. Python (Flask web app)")
    print(f"  2. Rust ({RUST_IMPLEMENTATION_STATUS})")
    
    while True:
        try:
            choice = input(f"\n{Colors.OKCYAN}Enter your choice (1 or 2): {Colors.ENDC}").strip()
        except EOFError:
            print_error("\nNo input received. Exiting.")
            sys.exit(1)
        
        if choice == "1":
            success = setup_python()
            break
        elif choice == "2":
            success = setup_rust()
            break
        else:
            print_error("Invalid choice. Please enter 1 or 2.")
    
    print()
    if success:
        print_header("Setup Complete!")
        print(f"{Colors.OKGREEN}ArchieAI has been set up successfully!{Colors.ENDC}\n")
    else:
        print_header("Setup Failed")
        print(f"{Colors.FAIL}Setup encountered errors. Please check the messages above.{Colors.ENDC}\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Setup cancelled by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)# src/helpers/scraper.py