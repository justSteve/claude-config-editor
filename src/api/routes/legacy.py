"""
Legacy UI API endpoints for backwards compatibility.

These endpoints support the original v1.0 web UI (index.html) which provides
direct editing of Claude configuration files.
"""

import json
import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class ConfigInfo(BaseModel):
    """Configuration file information."""
    id: str
    name: str
    path: str
    type: str
    active: bool


class SwitchConfigRequest(BaseModel):
    """Request to switch active configuration."""
    config_id: str


def detect_configs() -> Dict[str, Dict[str, any]]:
    """
    Detect available Claude configuration files.

    Returns:
        Dictionary of available configurations
    """
    configs = {}

    # Claude Code config
    claude_code_path = Path.home() / '.claude.json'
    if claude_code_path.exists():
        configs['code'] = {
            'path': claude_code_path,
            'name': 'Claude Code (CLI)',
            'type': 'code'
        }

    # Claude Desktop config
    if platform.system() == 'Darwin':  # macOS
        claude_desktop_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    elif platform.system() == 'Windows':
        claude_desktop_path = Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json'
    else:  # Linux
        claude_desktop_path = Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'

    if claude_desktop_path.exists():
        configs['desktop'] = {
            'path': claude_desktop_path,
            'name': 'Claude Desktop',
            'type': 'desktop'
        }

    return configs


# Global state for active config (in-memory, will reset on server restart)
_active_config = None


def get_active_config() -> Dict[str, any]:
    """
    Get the currently active configuration.

    Returns:
        Active configuration dictionary

    Raises:
        HTTPException: If no configuration is available
    """
    global _active_config

    if _active_config is None:
        # Auto-select first available config
        configs = detect_configs()
        if not configs:
            raise HTTPException(status_code=404, detail="No Claude configuration files found")
        _active_config = list(configs.values())[0]

    return _active_config


@router.get("/configs")
async def list_configs() -> List[ConfigInfo]:
    """
    List all available Claude configuration files.

    Returns:
        List of available configurations
    """
    try:
        configs = detect_configs()
        active = get_active_config()

        config_list = [
            ConfigInfo(
                id=key,
                name=val['name'],
                path=str(val['path']),
                type=val['type'],
                active=(val['path'] == active['path'])
            )
            for key, val in configs.items()
        ]

        return config_list
    except Exception as e:
        logger.error(f"Error listing configs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch")
async def switch_config(request: SwitchConfigRequest) -> JSONResponse:
    """
    Switch the active configuration file.

    Args:
        request: Configuration switch request

    Returns:
        Success response with new active config path
    """
    global _active_config

    try:
        configs = detect_configs()

        if request.config_id not in configs:
            raise HTTPException(status_code=404, detail=f"Configuration '{request.config_id}' not found")

        _active_config = configs[request.config_id]

        return JSONResponse({
            "success": True,
            "config": str(_active_config['path'])
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config() -> JSONResponse:
    """
    Get the current active configuration file contents.

    Returns:
        Configuration file contents with metadata
    """
    try:
        active = get_active_config()

        with open(active['path'], 'r', encoding='utf-8') as f:
            config = json.load(f)

        return JSONResponse({
            'path': str(active['path']),
            'name': active['name'],
            'type': active['type'],
            'config': config
        })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        logger.error(f"Error reading config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_config(new_config: dict) -> JSONResponse:
    """
    Save updated configuration to the active configuration file.

    Creates a backup before saving.

    Args:
        new_config: New configuration content to save

    Returns:
        Success response
    """
    try:
        active = get_active_config()
        config_path = Path(active['path'])

        # Create backup
        backup_path = config_path.parent / f"{config_path.stem}.backup{config_path.suffix}"
        if config_path.exists():
            shutil.copy2(config_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Save new config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved config to: {config_path}")

        return JSONResponse({
            "success": True,
            "message": "Configuration saved successfully",
            "backup": str(backup_path)
        })
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project")
async def get_project_history(path: str) -> JSONResponse:
    """
    Export single project history as JSON.

    Args:
        path: Project path to export

    Returns:
        Project history data
    """
    try:
        active = get_active_config()

        with open(active['path'], 'r', encoding='utf-8') as f:
            config = json.load(f)

        if path in config.get('projects', {}):
            project_data = config['projects'][path]
            return JSONResponse(project_data)
        else:
            raise HTTPException(status_code=404, detail=f"Project '{path}' not found in configuration")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
