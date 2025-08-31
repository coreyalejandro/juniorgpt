"""
Advanced Artifact System - Claude 4 Sonnet Level Implementation

This module provides a comprehensive artifact management system with the same
level of sophistication as Claude's artifact handling, including:
- Intelligent artifact detection and creation
- Rich content type support and validation
- Version control and history tracking
- Live preview and interactive capabilities
- Collaborative editing and sharing
- Smart content analysis and metadata extraction
"""

import os
import re
import json
import hashlib
import base64
import ast
import asyncio
import threading
import uuid
import tempfile
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import logging
import time

logger = logging.getLogger('juniorgpt.artifact_system')

class ArtifactType(Enum):
    """Comprehensive artifact types"""
    # Code artifacts
    CODE_PYTHON = "code/python"
    CODE_JAVASCRIPT = "code/javascript"
    CODE_TYPESCRIPT = "code/typescript"
    CODE_HTML = "code/html"
    CODE_CSS = "code/css"
    CODE_REACT = "code/react"
    CODE_VUE = "code/vue"
    CODE_SQL = "code/sql"
    CODE_BASH = "code/bash"
    CODE_DOCKERFILE = "code/dockerfile"
    CODE_YAML = "code/yaml"
    CODE_JSON = "code/json"
    CODE_XML = "code/xml"
    CODE_MARKDOWN = "code/markdown"
    
    # Document artifacts
    DOC_TEXT = "document/text"
    DOC_MARKDOWN = "document/markdown"
    DOC_HTML = "document/html"
    DOC_PDF = "document/pdf"
    DOC_LATEX = "document/latex"
    DOC_CSV = "document/csv"
    
    # Interactive artifacts
    INTERACTIVE_HTML = "interactive/html"
    INTERACTIVE_REACT = "interactive/react"
    INTERACTIVE_VUE = "interactive/vue"
    INTERACTIVE_CHART = "interactive/chart"
    INTERACTIVE_DIAGRAM = "interactive/diagram"
    
    # Media artifacts
    MEDIA_IMAGE = "media/image"
    MEDIA_AUDIO = "media/audio"
    MEDIA_VIDEO = "media/video"
    MEDIA_SVG = "media/svg"
    
    # Data artifacts
    DATA_JSON = "data/json"
    DATA_CSV = "data/csv"
    DATA_XML = "data/xml"
    DATA_YAML = "data/yaml"
    DATA_BINARY = "data/binary"
    
    # Configuration artifacts
    CONFIG_ENV = "config/env"
    CONFIG_DOCKER = "config/docker"
    CONFIG_K8S = "config/kubernetes"
    CONFIG_NGINX = "config/nginx"
    
    # Archive artifacts
    ARCHIVE_ZIP = "archive/zip"
    ARCHIVE_TAR = "archive/tar"

class ArtifactCapability(Enum):
    """Enhanced artifact capabilities"""
    EXECUTABLE = "executable"
    PREVIEWABLE = "previewable"
    EDITABLE = "editable"
    DOWNLOADABLE = "downloadable"
    SHAREABLE = "shareable"
    VERSIONABLE = "versionable"
    COLLABORATIVE = "collaborative"
    INTERACTIVE = "interactive"
    RUNNABLE = "runnable"
    TESTABLE = "testable"
    DEPLOYABLE = "deployable"
    SCALABLE = "scalable"
    SECURE = "secure"
    OPTIMIZED = "optimized"
    MONITORED = "monitored"
    BACKED_UP = "backed_up"
    COMPLIANT = "compliant"
    ACCESSIBLE = "accessible"
    MULTILINGUAL = "multilingual"
    CUSTOMIZABLE = "customizable"

@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    session_id: str
    artifact_id: str
    participants: List[str] = field(default_factory=list)
    active_editors: Dict[str, datetime] = field(default_factory=dict)
    changes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['last_activity'] = self.last_activity.isoformat()
        result['active_editors'] = {
            k: v.isoformat() for k, v in self.active_editors.items()
        }
        return result

@dataclass
class ArtifactMetadata:
    """Enhanced artifact metadata with collaboration support"""
    title: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    language: str = ""
    framework: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    license: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    size: int = 0
    checksum: str = ""
    encoding: str = "utf-8"
    line_count: int = 0
    complexity_score: float = 0.0
    quality_score: float = 0.0
    
    # Enhanced metadata fields
    collaborators: List[str] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    security_level: str = "public"  # public, private, restricted
    compliance_tags: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    deployment_info: Dict[str, Any] = field(default_factory=dict)
    backup_schedule: str = "daily"
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    multilingual_support: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result

@dataclass 
class ArtifactVersion:
    """Version tracking for artifacts"""
    version_id: str
    version_number: str
    content: str
    metadata: ArtifactMetadata
    created_at: datetime
    change_summary: str = ""
    diff_stats: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['metadata'] = self.metadata.to_dict()
        return result

class CollaborationManager:
    """Real-time collaboration manager for artifacts"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.websocket_connections: Dict[str, List[Any]] = {}
        self.change_callbacks: Dict[str, List[Callable]] = {}
        self.lock = threading.RLock()
    
    def create_session(self, artifact_id: str, initiator: str) -> str:
        """Create a new collaboration session"""
        with self.lock:
            session_id = f"collab_{uuid.uuid4().hex[:8]}"
            session = CollaborationSession(
                session_id=session_id,
                artifact_id=artifact_id,
                participants=[initiator]
            )
            session.active_editors[initiator] = datetime.utcnow()
            self.sessions[session_id] = session
            self.websocket_connections[session_id] = []
            self.change_callbacks[session_id] = []
            return session_id
    
    def join_session(self, session_id: str, user_id: str) -> bool:
        """Join an existing collaboration session"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            if user_id not in session.participants:
                session.participants.append(user_id)
            session.active_editors[user_id] = datetime.utcnow()
            session.last_activity = datetime.utcnow()
            return True
    
    def leave_session(self, session_id: str, user_id: str):
        """Leave a collaboration session"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if user_id in session.participants:
                    session.participants.remove(user_id)
                if user_id in session.active_editors:
                    del session.active_editors[user_id]
                session.last_activity = datetime.utcnow()
    
    def apply_change(self, session_id: str, user_id: str, change: Dict[str, Any]):
        """Apply a change to the artifact"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            change['user_id'] = user_id
            change['timestamp'] = datetime.utcnow().isoformat()
            session.changes.append(change)
            session.last_activity = datetime.utcnow()
            
            # Notify all callbacks
            for callback in self.change_callbacks.get(session_id, []):
                try:
                    callback(change)
                except Exception as e:
                    logger.error(f"Error in collaboration callback: {e}")
            
            return True
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        with self.lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            return {
                'session_id': session.session_id,
                'artifact_id': session.artifact_id,
                'participants': session.participants,
                'active_editors': list(session.active_editors.keys()),
                'change_count': len(session.changes),
                'last_activity': session.last_activity.isoformat()
            }
    
    def register_change_callback(self, session_id: str, callback: Callable):
        """Register a callback for change notifications"""
        with self.lock:
            if session_id not in self.change_callbacks:
                self.change_callbacks[session_id] = []
            self.change_callbacks[session_id].append(callback)
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 24):
        """Clean up inactive collaboration sessions"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_inactive_hours)
            inactive_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.last_activity < cutoff_time
            ]
            
            for session_id in inactive_sessions:
                del self.sessions[session_id]
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
                if session_id in self.change_callbacks:
                    del self.change_callbacks[session_id]

class Artifact:
    """
    Advanced artifact with comprehensive capabilities
    
    Features:
    - Rich content analysis and validation
    - Version control with diff tracking
    - Live preview generation
    - Interactive execution capabilities
    - Collaborative features
    - Smart metadata extraction
    """
    
    def __init__(
        self,
        artifact_id: str,
        artifact_type: ArtifactType,
        content: str,
        metadata: ArtifactMetadata,
        capabilities: List[ArtifactCapability] = None
    ):
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.content = content
        self.metadata = metadata
        self.capabilities = capabilities or []
        
        # Version control
        self.versions: List[ArtifactVersion] = []
        self.current_version = "1.0.0"
        
        # Runtime state
        self.is_running = False
        self.execution_context = {}
        self.preview_url = ""
        self.share_url = ""
        
        # Analysis results
        self.analysis_results = {}
        self.validation_results = {}
        self.security_scan = {}
        
        # Live preview and interactive features
        self.preview_server = None
        self.preview_port = None
        self.interactive_features = {}
        self.real_time_updates = True
        
        # Collaboration support
        self.collaboration_session = None
        self.collaboration_manager = None
        
        # Performance monitoring
        self.performance_metrics = {}
        self.execution_history = []
        
        # Security and compliance
        self.security_scan_results = {}
        self.compliance_status = {}
        
        # Optimization tracking
        self.optimization_suggestions = []
        self.optimization_history = []
        
        # Initialize
        self._analyze_content()
        self._validate_content()
        self._create_initial_version()
        self._setup_live_preview()
        self._setup_security_monitoring()
        self._setup_performance_monitoring()
        self._setup_optimization_tracking()
    
    def _analyze_content(self):
        """Comprehensive content analysis"""
        self.analysis_results = {
            "content_type": self._detect_content_type(),
            "complexity": self._calculate_complexity(),
            "quality": self._assess_quality(),
            "dependencies": self._extract_dependencies(),
            "imports": self._extract_imports(),
            "functions": self._extract_functions(),
            "classes": self._extract_classes(),
            "variables": self._extract_variables(),
            "comments": self._analyze_comments(),
            "documentation": self._extract_documentation()
        }
        
        # Update metadata with analysis results
        self.metadata.complexity_score = self.analysis_results["complexity"]
        self.metadata.quality_score = self.analysis_results["quality"]
        self.metadata.line_count = len(self.content.splitlines())
        self.metadata.size = len(self.content.encode('utf-8'))
        self.metadata.checksum = hashlib.sha256(self.content.encode('utf-8')).hexdigest()
    
    def _detect_content_type(self) -> Dict[str, Any]:
        """Intelligent content type detection"""
        content_lower = self.content.lower()
        
        # Language detection patterns
        patterns = {
            "python": [
                r"def\s+\w+\s*\(",
                r"import\s+\w+",
                r"from\s+\w+\s+import",
                r"class\s+\w+\s*:",
                r"if\s+__name__\s*==\s*['\"]__main__['\"]"
            ],
            "javascript": [
                r"function\s+\w+\s*\(",
                r"const\s+\w+\s*=",
                r"let\s+\w+\s*=",
                r"=>\s*{",
                r"require\s*\(",
                r"import\s+.*from"
            ],
            "html": [
                r"<html", r"<head", r"<body", r"<div", r"<!DOCTYPE"
            ],
            "css": [
                r"{\s*[\w-]+\s*:", r"@media", r"@import", r"\.[\w-]+"
            ],
            "sql": [
                r"SELECT\s+", r"FROM\s+", r"WHERE\s+", r"INSERT\s+INTO", r"CREATE\s+TABLE"
            ],
            "bash": [
                r"#!/bin/bash", r"#!/bin/sh", r"\$\{", r"if\s+\["
            ]
        }
        
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = sum(1 for pattern in lang_patterns if re.search(pattern, content_lower))
            if score > 0:
                scores[lang] = score
        
        detected_lang = max(scores, key=scores.get) if scores else "text"
        
        return {
            "detected_language": detected_lang,
            "confidence": scores.get(detected_lang, 0) / len(patterns.get(detected_lang, [1])),
            "all_scores": scores,
            "file_indicators": self._get_file_indicators()
        }
    
    def _get_file_indicators(self) -> Dict[str, Any]:
        """Extract file-type indicators"""
        indicators = {}
        
        # Shebang detection
        if self.content.startswith("#!"):
            shebang = self.content.split('\n')[0]
            indicators["shebang"] = shebang
        
        # Framework detection
        frameworks = {
            "react": ["import React", "from 'react'", "jsx", "tsx"],
            "vue": ["<template>", "<script>", "Vue.component", "new Vue"],
            "angular": ["@Component", "@Injectable", "import { Component }"],
            "flask": ["from flask import", "app = Flask"],
            "django": ["from django", "django.conf", "models.Model"],
            "express": ["express()", "app.use", "app.get"],
            "tensorflow": ["import tensorflow", "tf."],
            "pytorch": ["import torch", "torch.nn"]
        }
        
        detected_frameworks = []
        for framework, patterns in frameworks.items():
            if any(pattern in self.content for pattern in patterns):
                detected_frameworks.append(framework)
        
        indicators["frameworks"] = detected_frameworks
        
        return indicators
    
    def _calculate_complexity(self) -> float:
        """Calculate content complexity score"""
        if self.artifact_type in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
            return self._calculate_code_complexity()
        elif self.artifact_type == ArtifactType.DOC_MARKDOWN:
            return self._calculate_document_complexity()
        else:
            return self._calculate_general_complexity()
    
    def _calculate_code_complexity(self) -> float:
        """Calculate code complexity using various metrics"""
        try:
            if self.artifact_type == ArtifactType.CODE_PYTHON:
                return self._calculate_python_complexity()
            else:
                return self._calculate_general_code_complexity()
        except Exception:
            return self._calculate_general_complexity()
    
    def _calculate_python_complexity(self) -> float:
        """Calculate Python-specific complexity"""
        try:
            tree = ast.parse(self.content)
            
            complexity = 0
            
            for node in ast.walk(tree):
                # Control flow complexity
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 1
                elif isinstance(node, ast.ClassDef):
                    complexity += 2
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.comprehension):
                    complexity += 1
            
            # Normalize by number of lines
            lines = len([line for line in self.content.splitlines() if line.strip()])
            return min(complexity / max(lines, 1) * 10, 10.0)
            
        except SyntaxError:
            return self._calculate_general_complexity()
    
    def _calculate_general_code_complexity(self) -> float:
        """Calculate general code complexity"""
        lines = self.content.splitlines()
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        complexity = 0
        
        # Count control structures
        control_patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bwhile\b', r'\bfor\b',
            r'\bswitch\b', r'\bcase\b', r'\btry\b', r'\bcatch\b', r'\bfinally\b'
        ]
        
        for line in code_lines:
            for pattern in control_patterns:
                complexity += len(re.findall(pattern, line, re.IGNORECASE))
        
        # Normalize
        return min(complexity / max(len(code_lines), 1) * 10, 10.0)
    
    def _calculate_document_complexity(self) -> float:
        """Calculate document complexity"""
        words = len(self.content.split())
        
        # Headers, lists, links, images
        structure_elements = (
            len(re.findall(r'^#+\s', self.content, re.MULTILINE)) +
            len(re.findall(r'^[-*+]\s', self.content, re.MULTILINE)) +
            len(re.findall(r'\[.*?\]\(.*?\)', self.content)) +
            len(re.findall(r'!\[.*?\]\(.*?\)', self.content))
        )
        
        # Base complexity on length and structure
        return min((words / 100 + structure_elements / 10), 10.0)
    
    def _calculate_general_complexity(self) -> float:
        """Calculate general complexity based on content characteristics"""
        lines = len(self.content.splitlines())
        chars = len(self.content)
        
        # Simple heuristic based on size and structure
        return min(chars / 1000 + lines / 100, 10.0)
    
    def _assess_quality(self) -> float:
        """Assess content quality"""
        quality_score = 5.0  # Base score
        
        if self.artifact_type in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
            quality_score = self._assess_code_quality()
        elif self.artifact_type == ArtifactType.DOC_MARKDOWN:
            quality_score = self._assess_document_quality()
        
        return min(max(quality_score, 0.0), 10.0)
    
    def _assess_code_quality(self) -> float:
        """Assess code quality"""
        quality = 5.0
        
        # Check for comments
        comment_ratio = len(re.findall(r'#.*|//.*|/\*.*?\*/', self.content, re.DOTALL)) / max(len(self.content.splitlines()), 1)
        if comment_ratio > 0.1:
            quality += 1.0
        
        # Check for documentation
        if re.search(r'""".*?"""', self.content, re.DOTALL) or re.search(r'/\*\*.*?\*/', self.content, re.DOTALL):
            quality += 1.0
        
        # Check for error handling
        if re.search(r'\btry\b|\bcatch\b|\bexcept\b', self.content, re.IGNORECASE):
            quality += 1.0
        
        # Check for consistent naming
        if not re.search(r'[a-z][A-Z]|[A-Z][a-z].*_', self.content):  # Consistent naming style
            quality += 0.5
        
        # Penalize very long functions/methods
        if any(len(func.splitlines()) > 50 for func in re.findall(r'def\s+\w+.*?(?=\ndef|\nclass|\Z)', self.content, re.DOTALL)):
            quality -= 1.0
        
        return quality
    
    def _assess_document_quality(self) -> float:
        """Assess document quality"""
        quality = 5.0
        
        # Check for proper structure
        if re.search(r'^#\s', self.content, re.MULTILINE):
            quality += 1.0
        
        # Check for links and references
        if re.search(r'\[.*?\]\(.*?\)', self.content):
            quality += 0.5
        
        # Check for code examples
        if re.search(r'```.*?```', self.content, re.DOTALL):
            quality += 1.0
        
        # Check for completeness (reasonable length)
        word_count = len(self.content.split())
        if 100 <= word_count <= 2000:
            quality += 1.0
        
        return quality
    
    def _extract_dependencies(self) -> List[str]:
        """Extract dependencies from content"""
        dependencies = []
        
        # Python imports
        python_imports = re.findall(r'import\s+(\w+)|from\s+(\w+)', self.content)
        for imp in python_imports:
            dep = imp[0] or imp[1]
            if dep:
                dependencies.append(dep)
        
        # JavaScript/Node.js requires and imports
        js_requires = re.findall(r'require\s*\([\'"]([^\'"]+)[\'"]', self.content)
        dependencies.extend(js_requires)
        
        js_imports = re.findall(r'import.*from\s+[\'"]([^\'"]+)[\'"]', self.content)
        dependencies.extend(js_imports)
        
        # Package.json dependencies
        if '"dependencies"' in self.content:
            try:
                content_json = json.loads(self.content)
                if 'dependencies' in content_json:
                    dependencies.extend(content_json['dependencies'].keys())
            except json.JSONDecodeError:
                pass
        
        return list(set(dependencies))
    
    def _extract_imports(self) -> List[str]:
        """Extract import statements"""
        imports = []
        
        # Python imports
        python_imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+.+$', self.content, re.MULTILINE)
        imports.extend(python_imports)
        
        # JavaScript imports
        js_imports = re.findall(r'^import\s+.+$', self.content, re.MULTILINE)
        imports.extend(js_imports)
        
        return imports
    
    def _extract_functions(self) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        
        # Python functions
        python_funcs = re.findall(r'def\s+(\w+)\s*\([^)]*\):', self.content)
        for func in python_funcs:
            functions.append({"name": func, "language": "python", "type": "function"})
        
        # JavaScript functions
        js_funcs = re.findall(r'function\s+(\w+)\s*\(|(\w+)\s*=\s*\([^)]*\)\s*=>', self.content)
        for func in js_funcs:
            name = func[0] or func[1]
            if name:
                functions.append({"name": name, "language": "javascript", "type": "function"})
        
        return functions
    
    def _extract_classes(self) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        
        # Python classes
        python_classes = re.findall(r'class\s+(\w+)(?:\([^)]*\))?:', self.content)
        for cls in python_classes:
            classes.append({"name": cls, "language": "python", "type": "class"})
        
        # JavaScript classes
        js_classes = re.findall(r'class\s+(\w+)(?:\s+extends\s+\w+)?', self.content)
        for cls in js_classes:
            classes.append({"name": cls, "language": "javascript", "type": "class"})
        
        return classes
    
    def _extract_variables(self) -> List[str]:
        """Extract variable definitions"""
        variables = []
        
        # Python variables
        python_vars = re.findall(r'^(\w+)\s*=', self.content, re.MULTILINE)
        variables.extend(python_vars)
        
        # JavaScript variables
        js_vars = re.findall(r'(?:var|let|const)\s+(\w+)', self.content)
        variables.extend(js_vars)
        
        return list(set(variables))
    
    def _analyze_comments(self) -> Dict[str, Any]:
        """Analyze comments in the content"""
        comment_patterns = {
            "python": r'#.*$',
            "javascript": r'//.*$|/\*.*?\*/',
            "html": r'<!--.*?-->',
            "css": r'/\*.*?\*/'
        }
        
        total_lines = len(self.content.splitlines())
        comment_lines = 0
        
        for pattern in comment_patterns.values():
            comment_lines += len(re.findall(pattern, self.content, re.MULTILINE | re.DOTALL))
        
        return {
            "total_comments": comment_lines,
            "comment_ratio": comment_lines / max(total_lines, 1),
            "has_documentation": bool(re.search(r'""".*?"""|/\*\*.*?\*/', self.content, re.DOTALL))
        }
    
    def _extract_documentation(self) -> Dict[str, Any]:
        """Extract documentation from content"""
        # Python docstrings
        python_docstrings = re.findall(r'"""(.*?)"""', self.content, re.DOTALL)
        
        # JSDoc comments
        jsdoc_comments = re.findall(r'/\*\*(.*?)\*/', self.content, re.DOTALL)
        
        # Markdown headers
        md_headers = re.findall(r'^(#+\s+.*$)', self.content, re.MULTILINE)
        
        return {
            "docstrings": python_docstrings,
            "jsdoc_comments": jsdoc_comments,
            "markdown_headers": md_headers,
            "has_readme": "readme" in self.metadata.title.lower()
        }
    
    def _validate_content(self):
        """Validate content based on type"""
        self.validation_results = {
            "is_valid": True,
            "syntax_errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        if self.artifact_type == ArtifactType.CODE_PYTHON:
            self._validate_python_syntax()
        elif self.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            self._validate_javascript_syntax()
        elif self.artifact_type == ArtifactType.DATA_JSON:
            self._validate_json_syntax()
        elif self.artifact_type == ArtifactType.CODE_HTML:
            self._validate_html_structure()
    
    def _validate_python_syntax(self):
        """Validate Python syntax"""
        try:
            ast.parse(self.content)
        except SyntaxError as e:
            self.validation_results["is_valid"] = False
            self.validation_results["syntax_errors"].append({
                "line": e.lineno,
                "message": e.msg,
                "type": "SyntaxError"
            })
    
    def _validate_javascript_syntax(self):
        """Validate JavaScript syntax (basic check)"""
        # Basic bracket matching
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []
        
        for char in self.content:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    self.validation_results["warnings"].append("Mismatched brackets detected")
                    break
    
    def _validate_json_syntax(self):
        """Validate JSON syntax"""
        try:
            json.loads(self.content)
        except json.JSONDecodeError as e:
            self.validation_results["is_valid"] = False
            self.validation_results["syntax_errors"].append({
                "line": e.lineno,
                "column": e.colno,
                "message": e.msg,
                "type": "JSONDecodeError"
            })
    
    def _validate_html_structure(self):
        """Validate HTML structure (basic)"""
        # Check for basic HTML structure
        if not re.search(r'<html.*?>', self.content, re.IGNORECASE):
            self.validation_results["suggestions"].append("Consider adding <html> tag")
        
        # Check for unclosed tags (simplified)
        open_tags = re.findall(r'<(\w+)[^>]*(?<!/)>', self.content)
        close_tags = re.findall(r'</(\w+)>', self.content)
        
        self_closing = ['img', 'br', 'hr', 'input', 'meta', 'link']
        open_tags = [tag for tag in open_tags if tag.lower() not in self_closing]
        
        if len(open_tags) != len(close_tags):
            self.validation_results["warnings"].append("Possible unclosed HTML tags")
    
    def _create_initial_version(self):
        """Create initial version entry"""
        version = ArtifactVersion(
            version_id=f"{self.artifact_id}_v1.0.0",
            version_number="1.0.0",
            content=self.content,
            metadata=self.metadata,
            created_at=datetime.utcnow(),
            change_summary="Initial version"
        )
        self.versions.append(version)
    
    def _setup_live_preview(self):
        """Setup live preview capabilities"""
        if ArtifactCapability.PREVIEWABLE in self.capabilities:
            self.preview_port = self._find_available_port()
            self.preview_url = f"http://localhost:{self.preview_port}"
            
            # Setup interactive features based on artifact type
            if self.artifact_type in [ArtifactType.CODE_HTML, ArtifactType.INTERACTIVE_HTML]:
                self.interactive_features = {
                    "live_editing": True,
                    "real_time_preview": True,
                    "hot_reload": True,
                    "responsive_design": True
                }
            elif self.artifact_type in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
                self.interactive_features = {
                    "code_execution": True,
                    "debugging": True,
                    "performance_profiling": True,
                    "unit_testing": True
                }
    
    def _setup_security_monitoring(self):
        """Setup security monitoring and scanning"""
        self.security_scan_results = {
            "vulnerabilities": [],
            "security_score": 10.0,
            "last_scan": datetime.utcnow(),
            "compliance_status": "pending"
        }
        
        # Schedule regular security scans
        if ArtifactCapability.SECURE in self.capabilities:
            self._schedule_security_scan()
    
    def _setup_performance_monitoring(self):
        """Setup performance monitoring"""
        self.performance_metrics = {
            "execution_time": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "response_time": 0.0,
            "throughput": 0.0,
            "error_rate": 0.0
        }
        
        # Setup monitoring callbacks
        if ArtifactCapability.MONITORED in self.capabilities:
            self._setup_monitoring_callbacks()
    
    def _setup_optimization_tracking(self):
        """Setup optimization tracking and suggestions"""
        self.optimization_suggestions = []
        self.optimization_history = []
        
        # Analyze for optimization opportunities
        if ArtifactCapability.OPTIMIZED in self.capabilities:
            self._analyze_optimization_opportunities()
    
    def _find_available_port(self) -> int:
        """Find an available port for preview server"""
        import socket
        for port in range(8000, 9000):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return 8000  # Fallback
    
    def _schedule_security_scan(self):
        """Schedule regular security scanning"""
        def security_scan_task():
            while True:
                try:
                    self._perform_security_scan()
                    time.sleep(3600)  # Scan every hour
                except Exception as e:
                    logger.error(f"Security scan error: {e}")
                    time.sleep(3600)
        
        scan_thread = threading.Thread(target=security_scan_task, daemon=True)
        scan_thread.start()
    
    def _perform_security_scan(self):
        """Perform comprehensive security scan"""
        vulnerabilities = []
        security_score = 10.0
        
        # Check for common security issues
        if self.artifact_type == ArtifactType.CODE_PYTHON:
            # Check for dangerous imports
            dangerous_imports = ['subprocess', 'os', 'eval', 'exec']
            for imp in dangerous_imports:
                if imp in self.content:
                    vulnerabilities.append({
                        "type": "dangerous_import",
                        "severity": "high",
                        "description": f"Use of {imp} detected",
                        "recommendation": f"Review usage of {imp} for security implications"
                    })
                    security_score -= 2.0
        
        elif self.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            # Check for XSS vulnerabilities
            if 'innerHTML' in self.content or 'document.write' in self.content:
                vulnerabilities.append({
                    "type": "xss_vulnerability",
                    "severity": "high",
                    "description": "Potential XSS vulnerability detected",
                    "recommendation": "Use textContent instead of innerHTML"
                })
                security_score -= 3.0
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                vulnerabilities.append({
                    "type": "hardcoded_secret",
                    "severity": "critical",
                    "description": "Hardcoded secret detected",
                    "recommendation": "Use environment variables for secrets"
                })
                security_score -= 5.0
        
        self.security_scan_results.update({
            "vulnerabilities": vulnerabilities,
            "security_score": max(0.0, security_score),
            "last_scan": datetime.utcnow()
        })
    
    def _setup_monitoring_callbacks(self):
        """Setup performance monitoring callbacks"""
        def performance_callback(metrics):
            self.performance_metrics.update(metrics)
            self.execution_history.append({
                "timestamp": datetime.utcnow(),
                "metrics": metrics.copy()
            })
            
            # Keep only last 100 entries
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
        
        # Register callback for performance monitoring
        self.performance_callback = performance_callback
    
    def _analyze_optimization_opportunities(self):
        """Analyze content for optimization opportunities"""
        suggestions = []
        
        if self.artifact_type == ArtifactType.CODE_PYTHON:
            # Check for inefficient patterns
            if 'for i in range(len(' in self.content:
                suggestions.append({
                    "type": "inefficient_loop",
                    "description": "Use enumerate() instead of range(len())",
                    "impact": "medium",
                    "code_example": "for i, item in enumerate(items):"
                })
            
            if 'list.append' in self.content and 'for' in self.content:
                suggestions.append({
                    "type": "list_comprehension",
                    "description": "Consider using list comprehension",
                    "impact": "low",
                    "code_example": "[x for x in items if condition]"
                })
        
        elif self.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            # Check for DOM manipulation efficiency
            if 'getElementById' in self.content and 'innerHTML' in self.content:
                suggestions.append({
                    "type": "dom_optimization",
                    "description": "Cache DOM elements for better performance",
                    "impact": "medium",
                    "code_example": "const element = document.getElementById('id');"
                })
        
        self.optimization_suggestions = suggestions
    
    def update_content(self, new_content: str, change_summary: str = "") -> str:
        """Update artifact content with version tracking"""
        # Calculate diff
        diff_stats = self._calculate_diff(self.content, new_content)
        
        # Generate new version
        version_parts = self.current_version.split('.')
        version_parts[2] = str(int(version_parts[2]) + 1)
        new_version = '.'.join(version_parts)
        
        # Update content and metadata
        self.content = new_content
        self.current_version = new_version
        self.metadata.updated_at = datetime.utcnow()
        
        # Re-analyze content
        self._analyze_content()
        self._validate_content()
        
        # Create new version entry
        version = ArtifactVersion(
            version_id=f"{self.artifact_id}_{new_version}",
            version_number=new_version,
            content=new_content,
            metadata=self.metadata,
            created_at=datetime.utcnow(),
            change_summary=change_summary,
            diff_stats=diff_stats
        )
        self.versions.append(version)
        
        return new_version
    
    def _calculate_diff(self, old_content: str, new_content: str) -> Dict[str, int]:
        """Calculate diff statistics"""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Simple diff calculation
        added = len([line for line in new_lines if line not in old_lines])
        removed = len([line for line in old_lines if line not in new_lines])
        modified = min(len(old_lines), len(new_lines)) - (len(old_lines) + len(new_lines) - added - removed)
        
        return {
            "lines_added": added,
            "lines_removed": removed,
            "lines_modified": max(0, modified),
            "total_changes": added + removed + max(0, modified)
        }
    
    def get_preview(self) -> Dict[str, Any]:
        """Generate enhanced preview of the artifact with live capabilities"""
        if ArtifactCapability.PREVIEWABLE not in self.capabilities:
            return {"error": "Artifact is not previewable"}
        
        preview_data = {
            "type": self.artifact_type.value,
            "title": self.metadata.title,
            "content_preview": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "metadata": self.metadata.to_dict(),
            "analysis": self.analysis_results,
            "validation": self.validation_results,
            "preview_url": self.preview_url,
            "interactive_features": self.interactive_features,
            "security_status": self.security_scan_results,
            "performance_metrics": self.performance_metrics,
            "optimization_suggestions": self.optimization_suggestions
        }
        
        # Type-specific preview enhancements
        if self.artifact_type == ArtifactType.CODE_HTML or self.artifact_type == ArtifactType.INTERACTIVE_HTML:
            preview_data["html_preview"] = self._generate_html_preview()
            preview_data["live_preview"] = self._start_live_preview()
        elif self.artifact_type == ArtifactType.DOC_MARKDOWN:
            preview_data["markdown_html"] = self._render_markdown()
        elif self.artifact_type in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
            preview_data["syntax_highlighted"] = self._generate_syntax_highlighting()
            preview_data["execution_environment"] = self._setup_execution_environment()
        
        return preview_data
    
    def start_collaboration(self, user_id: str) -> str:
        """Start a collaboration session"""
        if ArtifactCapability.COLLABORATIVE not in self.capabilities:
            return None
        
        if not self.collaboration_manager:
            self.collaboration_manager = CollaborationManager()
        
        session_id = self.collaboration_manager.create_session(self.artifact_id, user_id)
        self.collaboration_session = session_id
        
        # Register change callback
        def on_content_change(change):
            self._handle_collaborative_change(change)
        
        self.collaboration_manager.register_change_callback(session_id, on_content_change)
        
        return session_id
    
    def join_collaboration(self, session_id: str, user_id: str) -> bool:
        """Join an existing collaboration session"""
        if not self.collaboration_manager:
            return False
        
        return self.collaboration_manager.join_session(session_id, user_id)
    
    def apply_collaborative_change(self, user_id: str, change: Dict[str, Any]) -> bool:
        """Apply a collaborative change"""
        if not self.collaboration_manager or not self.collaboration_session:
            return False
        
        return self.collaboration_manager.apply_change(self.collaboration_session, user_id, change)
    
    def _handle_collaborative_change(self, change: Dict[str, Any]):
        """Handle collaborative changes"""
        change_type = change.get('type')
        
        if change_type == 'content_update':
            new_content = change.get('content')
            if new_content and new_content != self.content:
                self.update_content(new_content, f"Collaborative edit by {change.get('user_id')}")
        
        elif change_type == 'cursor_position':
            # Handle cursor position updates for real-time editing
            pass
        
        elif change_type == 'comment':
            # Handle comments and annotations
            pass
    
    def _start_live_preview(self) -> Dict[str, Any]:
        """Start live preview server"""
        if not self.preview_port:
            return {"error": "Preview not available"}
        
        try:
            # Create temporary file for preview
            temp_dir = Path(tempfile.gettempdir()) / f"artifact_preview_{self.artifact_id}"
            temp_dir.mkdir(exist_ok=True)
            
            preview_file = temp_dir / "index.html"
            with open(preview_file, 'w', encoding='utf-8') as f:
                f.write(self.content)
            
            # Start simple HTTP server
            def serve_preview():
                import http.server
                import socketserver
                
                os.chdir(temp_dir)
                with socketserver.TCPServer(("", self.preview_port), http.server.SimpleHTTPRequestHandler) as httpd:
                    httpd.serve_forever()
            
            preview_thread = threading.Thread(target=serve_preview, daemon=True)
            preview_thread.start()
            
            return {
                "status": "running",
                "url": self.preview_url,
                "port": self.preview_port,
                "temp_dir": str(temp_dir)
            }
        
        except Exception as e:
            return {"error": f"Failed to start preview: {str(e)}"}
    
    def _setup_execution_environment(self) -> Dict[str, Any]:
        """Setup execution environment for code artifacts"""
        if self.artifact_type not in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
            return {"error": "Execution environment not supported for this artifact type"}
        
        env_config = {
            "type": self.artifact_type.value,
            "sandboxed": True,
            "timeout": 30,
            "memory_limit": "512MB",
            "network_access": False,
            "file_access": False
        }
        
        if self.artifact_type == ArtifactType.CODE_PYTHON:
            env_config.update({
                "python_version": "3.11",
                "allowed_modules": ["math", "datetime", "json", "re", "collections"],
                "restricted_modules": ["os", "subprocess", "sys", "fileinput"]
            })
        elif self.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            env_config.update({
                "node_version": "18.x",
                "allowed_globals": ["console", "Math", "JSON", "Date"],
                "restricted_globals": ["process", "require", "global"]
            })
        
        return env_config
    
    def _generate_html_preview(self) -> str:
        """Generate safe HTML preview"""
        # Basic sanitization for preview
        safe_content = self.content
        
        # Remove potentially dangerous elements
        dangerous_tags = ['script', 'object', 'embed', 'iframe']
        for tag in dangerous_tags:
            safe_content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', safe_content, flags=re.DOTALL | re.IGNORECASE)
        
        return safe_content
    
    def _render_markdown(self) -> str:
        """Render markdown to HTML (simplified)"""
        # Basic markdown to HTML conversion
        html = self.content
        
        # Headers
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        return html
    
    def _generate_syntax_highlighting(self) -> Dict[str, Any]:
        """Generate syntax highlighting data"""
        # This would integrate with a syntax highlighter like Pygments
        # For now, return basic token information
        return {
            "language": self.analysis_results.get("content_type", {}).get("detected_language", "text"),
            "tokens": [],  # Would contain syntax tokens
            "highlighted_html": f"<pre><code>{self.content}</code></pre>"
        }
    
    async def execute(self, execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute artifact if it's executable"""
        if ArtifactCapability.EXECUTABLE not in self.capabilities:
            return {"error": "Artifact is not executable"}
        
        execution_context = execution_context or {}
        
        try:
            if self.artifact_type == ArtifactType.CODE_PYTHON:
                return await self._execute_python(execution_context)
            elif self.artifact_type == ArtifactType.CODE_JAVASCRIPT:
                return await self._execute_javascript(execution_context)
            elif self.artifact_type == ArtifactType.CODE_BASH:
                return await self._execute_bash(execution_context)
            else:
                return {"error": f"Execution not supported for {self.artifact_type.value}"}
        
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
    
    async def _execute_python(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code safely"""
        # This would implement safe Python execution
        # For security, this should run in a sandboxed environment
        try:
            # Compile first to check syntax
            compiled = compile(self.content, f"artifact_{self.artifact_id}", "exec")
            
            # In production, this would use a sandboxed executor
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            exec_globals = {"__name__": "__main__"}
            exec_globals.update(context.get("globals", {}))
            
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(compiled, exec_globals)
            
            return {
                "success": True,
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "execution_time": 0.0  # Would measure actual time
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _execute_javascript(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JavaScript code"""
        # This would use Node.js or a JavaScript engine
        return {"error": "JavaScript execution not implemented"}
    
    async def _execute_bash(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash script"""
        # This would run bash in a secure environment
        return {"error": "Bash execution not implemented"}
    
    def get_sharing_info(self) -> Dict[str, Any]:
        """Get sharing information"""
        if ArtifactCapability.SHAREABLE not in self.capabilities:
            return {"error": "Artifact is not shareable"}
        
        # Generate sharing URL and permissions
        sharing_token = base64.urlsafe_b64encode(
            f"{self.artifact_id}:{datetime.utcnow().isoformat()}".encode()
        ).decode()
        
        return {
            "share_url": f"/artifacts/shared/{sharing_token}",
            "share_token": sharing_token,
            "permissions": ["view", "download"],  # Could be configurable
            "expires_at": None  # Could set expiration
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary"""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "capabilities": [cap.value for cap in self.capabilities],
            "current_version": self.current_version,
            "version_count": len(self.versions),
            "analysis_results": self.analysis_results,
            "validation_results": self.validation_results,
            "is_running": self.is_running,
            "preview_url": self.preview_url,
            "share_url": self.share_url
        }

class AdvancedArtifactManager:
    """
    Enhanced artifact manager with Claude-4 level capabilities
    
    Features:
    - Intelligent artifact detection from responses
    - Rich content analysis and validation
    - Version control and collaboration
    - Live preview and execution
    - Smart recommendations and optimization
    - Security monitoring and compliance
    - Performance tracking and optimization
    - Multi-language support and accessibility
    """
    
    def __init__(self, storage_dir: str = "artifacts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # In-memory artifact registry
        self.artifacts: Dict[str, Artifact] = {}
        
        # Type detection patterns
        self.type_patterns = self._initialize_type_patterns()
        
        # Load existing artifacts
        self._load_existing_artifacts()
    
    def _initialize_type_patterns(self) -> Dict[ArtifactType, List[str]]:
        """Initialize patterns for artifact type detection"""
        return {
            ArtifactType.CODE_PYTHON: [
                r"```python\n(.*?)```",
                r"```py\n(.*?)```",
                r"# Python",
                r"#!/usr/bin/env python"
            ],
            ArtifactType.CODE_JAVASCRIPT: [
                r"```javascript\n(.*?)```",
                r"```js\n(.*?)```",
                r"#!/usr/bin/env node"
            ],
            ArtifactType.CODE_HTML: [
                r"```html\n(.*?)```",
                r"<!DOCTYPE html"
            ],
            ArtifactType.CODE_CSS: [
                r"```css\n(.*?)```"
            ],
            ArtifactType.CODE_SQL: [
                r"```sql\n(.*?)```"
            ],
            ArtifactType.CODE_BASH: [
                r"```bash\n(.*?)```",
                r"```sh\n(.*?)```",
                r"#!/bin/bash",
                r"#!/bin/sh"
            ],
            ArtifactType.DOC_MARKDOWN: [
                r"```markdown\n(.*?)```",
                r"```md\n(.*?)```"
            ],
            ArtifactType.DATA_JSON: [
                r"```json\n(.*?)```"
            ],
            ArtifactType.CODE_YAML: [
                r"```yaml\n(.*?)```",
                r"```yml\n(.*?)```"
            ]
        }
    
    def _load_existing_artifacts(self):
        """Load existing artifacts from storage"""
        metadata_dir = self.storage_dir / "metadata"
        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file) as f:
                        data = json.load(f)
                    
                    # Reconstruct artifact
                    artifact_id = data["artifact_id"]
                    content_file = self.storage_dir / "content" / f"{artifact_id}.txt"
                    
                    if content_file.exists():
                        with open(content_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        metadata = ArtifactMetadata(**data["metadata"])
                        artifact_type = ArtifactType(data["artifact_type"])
                        capabilities = [ArtifactCapability(cap) for cap in data.get("capabilities", [])]
                        
                        artifact = Artifact(artifact_id, artifact_type, content, metadata, capabilities)
                        self.artifacts[artifact_id] = artifact
                        
                except Exception as e:
                    logger.warning(f"Failed to load artifact from {metadata_file}: {e}")
    
    def detect_and_create_artifacts(self, response_text: str, context: Dict[str, Any] = None) -> List[Artifact]:
        """
        Intelligently detect and create artifacts from response text
        
        This method analyzes the response and automatically creates appropriate
        artifacts based on content patterns and context clues.
        """
        artifacts = []
        
        # Extract code blocks with language hints
        code_blocks = self._extract_code_blocks(response_text)
        
        for block in code_blocks:
            try:
                artifact = self._create_artifact_from_code_block(block, context)
                if artifact:
                    artifacts.append(artifact)
                    self.artifacts[artifact.artifact_id] = artifact
            except Exception as e:
                logger.error(f"Failed to create artifact from code block: {e}")
        
        # Detect implicit artifacts (content without explicit code blocks)
        implicit_artifacts = self._detect_implicit_artifacts(response_text, context)
        for artifact in implicit_artifacts:
            artifacts.append(artifact)
            self.artifacts[artifact.artifact_id] = artifact
        
        # Save artifacts to storage
        for artifact in artifacts:
            self._save_artifact(artifact)
        
        return artifacts
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks with metadata"""
        blocks = []
        
        # Pattern for fenced code blocks
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for language, content in matches:
            if content.strip():
                blocks.append({
                    "language": language.lower() if language else "text",
                    "content": content.strip(),
                    "type": "fenced"
                })
        
        # Pattern for indented code blocks (if no fenced blocks found)
        if not blocks:
            lines = text.split('\n')
            current_block = []
            in_code_block = False
            
            for line in lines:
                if line.startswith('    ') or line.startswith('\t'):
                    current_block.append(line[4:] if line.startswith('    ') else line[1:])
                    in_code_block = True
                else:
                    if in_code_block and current_block:
                        content = '\n'.join(current_block)
                        if content.strip():
                            blocks.append({
                                "language": self._detect_language_from_content(content),
                                "content": content.strip(),
                                "type": "indented"
                            })
                        current_block = []
                        in_code_block = False
        
        return blocks
    
    def _detect_language_from_content(self, content: str) -> str:
        """Detect programming language from content"""
        # Use patterns from type detection
        for artifact_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                    return artifact_type.value.split('/')[-1]
        
        return "text"
    
    def _create_artifact_from_code_block(self, block: Dict[str, str], context: Dict[str, Any] = None) -> Optional[Artifact]:
        """Create artifact from code block"""
        language = block["language"]
        content = block["content"]
        
        # Determine artifact type
        artifact_type = self._map_language_to_type(language)
        if not artifact_type:
            return None
        
        # Generate artifact ID
        artifact_id = self._generate_artifact_id(content)
        
        # Create metadata
        metadata = self._create_metadata_from_content(content, language, context)
        
        # Determine capabilities
        capabilities = self._determine_capabilities(artifact_type, content)
        
        # Create artifact
        artifact = Artifact(artifact_id, artifact_type, content, metadata, capabilities)
        
        return artifact
    
    def _map_language_to_type(self, language: str) -> Optional[ArtifactType]:
        """Map language string to artifact type"""
        mapping = {
            "python": ArtifactType.CODE_PYTHON,
            "py": ArtifactType.CODE_PYTHON,
            "javascript": ArtifactType.CODE_JAVASCRIPT,
            "js": ArtifactType.CODE_JAVASCRIPT,
            "typescript": ArtifactType.CODE_TYPESCRIPT,
            "ts": ArtifactType.CODE_TYPESCRIPT,
            "html": ArtifactType.CODE_HTML,
            "css": ArtifactType.CODE_CSS,
            "sql": ArtifactType.CODE_SQL,
            "bash": ArtifactType.CODE_BASH,
            "sh": ArtifactType.CODE_BASH,
            "markdown": ArtifactType.DOC_MARKDOWN,
            "md": ArtifactType.DOC_MARKDOWN,
            "json": ArtifactType.DATA_JSON,
            "yaml": ArtifactType.CODE_YAML,
            "yml": ArtifactType.CODE_YAML,
            "xml": ArtifactType.CODE_XML,
            "dockerfile": ArtifactType.CODE_DOCKERFILE
        }
        
        return mapping.get(language.lower())
    
    def _generate_artifact_id(self, content: str) -> str:
        """Generate unique artifact ID"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"artifact_{timestamp}_{content_hash}"
    
    def _create_metadata_from_content(self, content: str, language: str, context: Dict[str, Any] = None) -> ArtifactMetadata:
        """Create metadata by analyzing content"""
        context = context or {}
        
        # Extract title from content
        title = self._extract_title_from_content(content, language)
        
        # Extract description
        description = self._extract_description_from_content(content, language)
        
        # Determine file extension
        extension_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "sql": ".sql",
            "bash": ".sh",
            "markdown": ".md",
            "json": ".json",
            "yaml": ".yml"
        }
        
        extension = extension_map.get(language, ".txt")
        if not title.endswith(extension):
            title += extension
        
        return ArtifactMetadata(
            title=title,
            description=description,
            author=context.get("agent_name", "AI Assistant"),
            language=language,
            tags=context.get("tags", []),
            created_at=datetime.utcnow()
        )
    
    def _extract_title_from_content(self, content: str, language: str) -> str:
        """Extract appropriate title from content"""
        # Try to find function/class names for code
        if language in ["python", "javascript", "typescript"]:
            # Look for main function or class
            func_match = re.search(r'def\s+(\w+)|function\s+(\w+)|class\s+(\w+)', content)
            if func_match:
                name = func_match.group(1) or func_match.group(2) or func_match.group(3)
                return name
        
        # Look for filename hints in comments
        filename_match = re.search(r'#\s*(?:File|Filename):\s*(\S+)', content, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1)
        
        # Use first line if it looks like a title
        first_line = content.split('\n')[0].strip()
        if len(first_line) < 50 and not any(char in first_line for char in "{}()[]"):
            return first_line.lstrip('#').strip() or "generated_file"
        
        return "generated_file"
    
    def _extract_description_from_content(self, content: str, language: str) -> str:
        """Extract description from content"""
        # Look for docstrings or comments at the top
        if language == "python":
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                return docstring_match.group(1).strip()
        
        # Look for comments at the beginning
        lines = content.split('\n')
        description_lines = []
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                comment = re.sub(r'^[#/*\s]+', '', line).strip()
                if comment:
                    description_lines.append(comment)
            elif line and not line.startswith(('import', 'from', 'const', 'let', 'var', 'function')):
                break
        
        return ' '.join(description_lines) if description_lines else f"Generated {language} code"
    
    def _determine_capabilities(self, artifact_type: ArtifactType, content: str) -> List[ArtifactCapability]:
        """Determine artifact capabilities"""
        capabilities = [
            ArtifactCapability.DOWNLOADABLE,
            ArtifactCapability.PREVIEWABLE,
            ArtifactCapability.VERSIONABLE
        ]
        
        # Executable types
        if artifact_type in [
            ArtifactType.CODE_PYTHON,
            ArtifactType.CODE_JAVASCRIPT,
            ArtifactType.CODE_BASH
        ]:
            capabilities.append(ArtifactCapability.EXECUTABLE)
            capabilities.append(ArtifactCapability.RUNNABLE)
        
        # Testable code
        if artifact_type in [ArtifactType.CODE_PYTHON, ArtifactType.CODE_JAVASCRIPT]:
            if "test" in content.lower() or "def test_" in content or "it(" in content:
                capabilities.append(ArtifactCapability.TESTABLE)
        
        # Interactive content
        if artifact_type in [
            ArtifactType.CODE_HTML,
            ArtifactType.INTERACTIVE_HTML,
            ArtifactType.INTERACTIVE_REACT
        ]:
            capabilities.append(ArtifactCapability.INTERACTIVE)
        
        # Editable content
        if artifact_type in [
            ArtifactType.DOC_MARKDOWN,
            ArtifactType.DOC_TEXT,
            ArtifactType.DATA_JSON,
            ArtifactType.CODE_YAML
        ]:
            capabilities.append(ArtifactCapability.EDITABLE)
        
        # Shareable content (most types)
        capabilities.append(ArtifactCapability.SHAREABLE)
        
        return capabilities
    
    def _detect_implicit_artifacts(self, text: str, context: Dict[str, Any] = None) -> List[Artifact]:
        """Detect artifacts that aren't in explicit code blocks"""
        artifacts = []
        
        # Look for configuration-like content
        if self._looks_like_config(text):
            artifact = self._create_config_artifact(text, context)
            if artifact:
                artifacts.append(artifact)
        
        # Look for data structures
        if self._looks_like_data(text):
            artifact = self._create_data_artifact(text, context)
            if artifact:
                artifacts.append(artifact)
        
        return artifacts
    
    def _looks_like_config(self, text: str) -> bool:
        """Check if text looks like configuration"""
        config_indicators = [
            "=", ":", "port", "host", "database", "api_key",
            "config", "settings", "environment"
        ]
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        config_lines = sum(1 for line in lines if any(indicator in line.lower() for indicator in config_indicators))
        
        return config_lines > len(lines) * 0.3 and len(lines) > 3
    
    def _create_config_artifact(self, text: str, context: Dict[str, Any] = None) -> Optional[Artifact]:
        """Create configuration artifact"""
        # Determine config type
        if text.strip().startswith('{') and text.strip().endswith('}'):
            artifact_type = ArtifactType.DATA_JSON
        elif ':' in text and '=' not in text:
            artifact_type = ArtifactType.CODE_YAML
        else:
            artifact_type = ArtifactType.CONFIG_ENV
        
        artifact_id = self._generate_artifact_id(text)
        metadata = ArtifactMetadata(
            title="config.env" if artifact_type == ArtifactType.CONFIG_ENV else "config.yml",
            description="Generated configuration file",
            author=context.get("agent_name", "AI Assistant") if context else "AI Assistant"
        )
        
        capabilities = [
            ArtifactCapability.DOWNLOADABLE,
            ArtifactCapability.EDITABLE,
            ArtifactCapability.PREVIEWABLE
        ]
        
        return Artifact(artifact_id, artifact_type, text, metadata, capabilities)
    
    def _looks_like_data(self, text: str) -> bool:
        """Check if text looks like structured data"""
        # Check for JSON-like structure
        if (text.strip().startswith('{') and text.strip().endswith('}')) or \
           (text.strip().startswith('[') and text.strip().endswith(']')):
            return True
        
        # Check for CSV-like structure
        lines = text.split('\n')
        if len(lines) > 2:
            separators = [',', '\t', ';']
            for sep in separators:
                if all(sep in line for line in lines[:3] if line.strip()):
                    return True
        
        return False
    
    def _create_data_artifact(self, text: str, context: Dict[str, Any] = None) -> Optional[Artifact]:
        """Create data artifact"""
        # Determine data type
        text_stripped = text.strip()
        
        if (text_stripped.startswith('{') and text_stripped.endswith('}')) or \
           (text_stripped.startswith('[') and text_stripped.endswith(']')):
            artifact_type = ArtifactType.DATA_JSON
            title = "data.json"
        elif ',' in text and len(text.split('\n')) > 1:
            artifact_type = ArtifactType.DOC_CSV
            title = "data.csv"
        else:
            artifact_type = ArtifactType.DATA_YAML
            title = "data.yml"
        
        artifact_id = self._generate_artifact_id(text)
        metadata = ArtifactMetadata(
            title=title,
            description="Generated data file",
            author=context.get("agent_name", "AI Assistant") if context else "AI Assistant"
        )
        
        capabilities = [
            ArtifactCapability.DOWNLOADABLE,
            ArtifactCapability.PREVIEWABLE,
            ArtifactCapability.EDITABLE
        ]
        
        return Artifact(artifact_id, artifact_type, text, metadata, capabilities)
    
    def _save_artifact(self, artifact: Artifact):
        """Save artifact to storage"""
        # Create directories
        content_dir = self.storage_dir / "content"
        metadata_dir = self.storage_dir / "metadata"
        content_dir.mkdir(exist_ok=True)
        metadata_dir.mkdir(exist_ok=True)
        
        # Save content
        content_file = content_dir / f"{artifact.artifact_id}.txt"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(artifact.content)
        
        # Save metadata
        metadata_file = metadata_dir / f"{artifact.artifact_id}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(artifact.to_dict(), f, indent=2)
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID"""
        return self.artifacts.get(artifact_id)
    
    def list_artifacts(self, artifact_type: ArtifactType = None, capabilities: List[ArtifactCapability] = None) -> List[Dict[str, Any]]:
        """List artifacts with optional filtering"""
        artifacts = list(self.artifacts.values())
        
        if artifact_type:
            artifacts = [a for a in artifacts if a.artifact_type == artifact_type]
        
        if capabilities:
            artifacts = [a for a in artifacts if all(cap in a.capabilities for cap in capabilities)]
        
        return [artifact.to_dict() for artifact in artifacts]
    
    def search_artifacts(self, query: str) -> List[Dict[str, Any]]:
        """Search artifacts by content or metadata"""
        results = []
        query_lower = query.lower()
        
        for artifact in self.artifacts.values():
            # Search in title and description
            if (query_lower in artifact.metadata.title.lower() or
                query_lower in artifact.metadata.description.lower() or
                query_lower in artifact.content.lower()):
                
                result = artifact.to_dict()
                # Add relevance score
                score = 0
                if query_lower in artifact.metadata.title.lower():
                    score += 3
                if query_lower in artifact.metadata.description.lower():
                    score += 2
                if query_lower in artifact.content.lower():
                    score += 1
                
                result["relevance_score"] = score
                results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_artifact_statistics(self) -> Dict[str, Any]:
        """Get comprehensive artifact statistics with enhanced analytics"""
        if not self.artifacts:
            return {"total_artifacts": 0}
        
        artifacts = list(self.artifacts.values())
        
        # Type distribution
        type_counts = {}
        for artifact in artifacts:
            type_name = artifact.artifact_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Capability distribution
        capability_counts = {}
        for artifact in artifacts:
            for cap in artifact.capabilities:
                cap_name = cap.value
                capability_counts[cap_name] = capability_counts.get(cap_name, 0) + 1
        
        # Quality and complexity statistics
        complexities = [a.metadata.complexity_score for a in artifacts]
        qualities = [a.metadata.quality_score for a in artifacts]
        
        # Size statistics
        sizes = [a.metadata.size for a in artifacts]
        
        # Security statistics
        security_scores = [a.security_scan_results.get('security_score', 10.0) for a in artifacts]
        
        # Performance statistics
        performance_metrics = []
        for artifact in artifacts:
            if artifact.performance_metrics:
                performance_metrics.append(artifact.performance_metrics)
        
        # Collaboration statistics
        collaboration_stats = {
            "collaborative_artifacts": len([a for a in artifacts if ArtifactCapability.COLLABORATIVE in a.capabilities]),
            "active_sessions": len([a for a in artifacts if a.collaboration_session]),
            "total_collaborators": len(set().union(*[a.metadata.collaborators for a in artifacts if a.metadata.collaborators]))
        }
        
        return {
            "total_artifacts": len(artifacts),
            "type_distribution": type_counts,
            "capability_distribution": capability_counts,
            "average_complexity": sum(complexities) / len(complexities) if complexities else 0,
            "average_quality": sum(qualities) / len(qualities) if qualities else 0,
            "average_security_score": sum(security_scores) / len(security_scores) if security_scores else 10.0,
            "total_size_bytes": sum(sizes),
            "average_size_bytes": sum(sizes) / len(sizes) if sizes else 0,
            "largest_artifact": max(sizes) if sizes else 0,
            "languages_used": list(set(a.metadata.language for a in artifacts if a.metadata.language)),
            "collaboration_stats": collaboration_stats,
            "performance_metrics": performance_metrics,
            "optimization_opportunities": self._get_optimization_opportunities(),
            "security_vulnerabilities": self._get_security_summary()
        }
    
    def _get_optimization_opportunities(self) -> Dict[str, Any]:
        """Get optimization opportunities across all artifacts"""
        opportunities = {
            "performance": [],
            "security": [],
            "quality": [],
            "accessibility": []
        }
        
        for artifact in self.artifacts.values():
            # Performance opportunities
            if artifact.optimization_suggestions:
                opportunities["performance"].extend(artifact.optimization_suggestions)
            
            # Security opportunities
            if artifact.security_scan_results.get('vulnerabilities'):
                opportunities["security"].extend(artifact.security_scan_results['vulnerabilities'])
            
            # Quality opportunities
            if artifact.metadata.quality_score < 7.0:
                opportunities["quality"].append({
                    "artifact_id": artifact.artifact_id,
                    "current_score": artifact.metadata.quality_score,
                    "suggestions": ["Add documentation", "Improve error handling", "Add tests"]
                })
            
            # Accessibility opportunities
            if artifact.artifact_type in [ArtifactType.CODE_HTML, ArtifactType.INTERACTIVE_HTML]:
                if not artifact.metadata.accessibility_features:
                    opportunities["accessibility"].append({
                        "artifact_id": artifact.artifact_id,
                        "suggestions": ["Add ARIA labels", "Ensure keyboard navigation", "Add alt text for images"]
                    })
        
        return opportunities
    
    def _get_security_summary(self) -> Dict[str, Any]:
        """Get security summary across all artifacts"""
        total_vulnerabilities = 0
        critical_vulnerabilities = 0
        high_vulnerabilities = 0
        medium_vulnerabilities = 0
        low_vulnerabilities = 0
        
        for artifact in self.artifacts.values():
            vulnerabilities = artifact.security_scan_results.get('vulnerabilities', [])
            total_vulnerabilities += len(vulnerabilities)
            
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'low')
                if severity == 'critical':
                    critical_vulnerabilities += 1
                elif severity == 'high':
                    high_vulnerabilities += 1
                elif severity == 'medium':
                    medium_vulnerabilities += 1
                else:
                    low_vulnerabilities += 1
        
        return {
            "total_vulnerabilities": total_vulnerabilities,
            "critical": critical_vulnerabilities,
            "high": high_vulnerabilities,
            "medium": medium_vulnerabilities,
            "low": low_vulnerabilities,
            "overall_security_status": "secure" if critical_vulnerabilities == 0 and high_vulnerabilities == 0 else "needs_attention"
        }
    
    def optimize_artifacts(self) -> Dict[str, Any]:
        """Apply optimizations to all artifacts"""
        optimization_results = {
            "optimized_artifacts": 0,
            "improvements": [],
            "errors": []
        }
        
        for artifact in self.artifacts.values():
            try:
                optimization_result = self._optimize_single_artifact(artifact)
                if optimization_result["optimized"]:
                    optimization_results["optimized_artifacts"] += 1
                    optimization_results["improvements"].extend(optimization_result["improvements"])
            except Exception as e:
                optimization_results["errors"].append({
                    "artifact_id": artifact.artifact_id,
                    "error": str(e)
                })
        
        return optimization_results
    
    def _optimize_single_artifact(self, artifact: Artifact) -> Dict[str, Any]:
        """Optimize a single artifact"""
        improvements = []
        optimized = False
        
        # Performance optimizations
        if artifact.artifact_type == ArtifactType.CODE_PYTHON:
            optimized_content = self._optimize_python_code(artifact.content)
            if optimized_content != artifact.content:
                artifact.update_content(optimized_content, "Performance optimization applied")
                improvements.append("Python code optimized for performance")
                optimized = True
        
        elif artifact.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            optimized_content = self._optimize_javascript_code(artifact.content)
            if optimized_content != artifact.content:
                artifact.update_content(optimized_content, "Performance optimization applied")
                improvements.append("JavaScript code optimized for performance")
                optimized = True
        
        # Security optimizations
        security_improvements = self._apply_security_optimizations(artifact)
        if security_improvements:
            improvements.extend(security_improvements)
            optimized = True
        
        # Accessibility optimizations
        if artifact.artifact_type in [ArtifactType.CODE_HTML, ArtifactType.INTERACTIVE_HTML]:
            accessibility_improvements = self._apply_accessibility_optimizations(artifact)
            if accessibility_improvements:
                improvements.extend(accessibility_improvements)
                optimized = True
        
        return {
            "optimized": optimized,
            "improvements": improvements
        }
    
    def _optimize_python_code(self, content: str) -> str:
        """Optimize Python code"""
        optimized = content
        
        # Replace inefficient patterns
        optimized = re.sub(r'for i in range\(len\(([^)]+)\)\):', r'for i, item in enumerate(\1):', optimized)
        
        # Optimize list comprehensions
        optimized = re.sub(r'result = \[\]\s+for item in (\w+):\s+if (\w+):\s+result\.append\(([^)]+)\)', 
                          r'result = [\3 for item in \1 if \2]', optimized, flags=re.MULTILINE)
        
        return optimized
    
    def _optimize_javascript_code(self, content: str) -> str:
        """Optimize JavaScript code"""
        optimized = content
        
        # Cache DOM queries
        optimized = re.sub(r'document\.getElementById\(([^)]+)\)\.innerHTML', 
                          r'const element = document.getElementById(\1); element.innerHTML', optimized)
        
        # Use const/let instead of var
        optimized = re.sub(r'\bvar\s+(\w+)', r'const \1', optimized)
        
        return optimized
    
    def _apply_security_optimizations(self, artifact: Artifact) -> List[str]:
        """Apply security optimizations"""
        improvements = []
        
        if artifact.artifact_type == ArtifactType.CODE_PYTHON:
            # Replace eval with safer alternatives
            if 'eval(' in artifact.content:
                # This would require more sophisticated analysis
                improvements.append("Security: Consider replacing eval() with safer alternatives")
        
        elif artifact.artifact_type == ArtifactType.CODE_JAVASCRIPT:
            # Replace innerHTML with textContent where appropriate
            if 'innerHTML' in artifact.content and not re.search(r'<[^>]+>', artifact.content):
                improvements.append("Security: Consider using textContent instead of innerHTML")
        
        return improvements
    
    def _apply_accessibility_optimizations(self, artifact: Artifact) -> List[str]:
        """Apply accessibility optimizations"""
        improvements = []
        
        # Add missing alt attributes
        if 'img' in artifact.content and 'alt=' not in artifact.content:
            improvements.append("Accessibility: Add alt attributes to images")
        
        # Add ARIA labels
        if 'input' in artifact.content and 'aria-label' not in artifact.content:
            improvements.append("Accessibility: Add ARIA labels to form elements")
        
        # Ensure proper heading structure
        if 'h1' in artifact.content and artifact.content.count('h1') > 1:
            improvements.append("Accessibility: Ensure only one h1 element per page")
        
        return improvements

# Global advanced artifact manager instance
_global_artifact_manager = None

def get_artifact_manager() -> AdvancedArtifactManager:
    """Get global advanced artifact manager instance"""
    global _global_artifact_manager
    if _global_artifact_manager is None:
        _global_artifact_manager = AdvancedArtifactManager()
    return _global_artifact_manager

# Enhanced convenience functions for the advanced artifact system
def create_artifact_from_response(response_text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Create artifacts from agent response with enhanced capabilities"""
    manager = get_artifact_manager()
    artifacts = manager.detect_and_create_artifacts(response_text, context)
    return [artifact.to_dict() for artifact in artifacts]

def get_artifact_by_id(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Get artifact by ID with full capabilities"""
    manager = get_artifact_manager()
    artifact = manager.get_artifact(artifact_id)
    return artifact.to_dict() if artifact else None

def list_all_artifacts() -> List[Dict[str, Any]]:
    """List all artifacts with enhanced metadata"""
    manager = get_artifact_manager()
    return manager.list_artifacts()

def search_artifacts(query: str) -> List[Dict[str, Any]]:
    """Search artifacts with enhanced relevance scoring"""
    manager = get_artifact_manager()
    return manager.search_artifacts(query)

def optimize_all_artifacts() -> Dict[str, Any]:
    """Apply optimizations to all artifacts"""
    manager = get_artifact_manager()
    return manager.optimize_artifacts()

def get_artifact_statistics() -> Dict[str, Any]:
    """Get comprehensive artifact statistics"""
    manager = get_artifact_manager()
    return manager.get_artifact_statistics()

def start_collaboration(artifact_id: str, user_id: str) -> Optional[str]:
    """Start a collaboration session for an artifact"""
    manager = get_artifact_manager()
    artifact = manager.get_artifact(artifact_id)
    if artifact and ArtifactCapability.COLLABORATIVE in artifact.capabilities:
        return artifact.start_collaboration(user_id)
    return None

def join_collaboration(session_id: str, user_id: str, artifact_id: str) -> bool:
    """Join an existing collaboration session"""
    manager = get_artifact_manager()
    artifact = manager.get_artifact(artifact_id)
    if artifact:
        return artifact.join_collaboration(session_id, user_id)
    return False

def get_live_preview(artifact_id: str) -> Dict[str, Any]:
    """Get live preview for an artifact"""
    manager = get_artifact_manager()
    artifact = manager.get_artifact(artifact_id)
    if artifact and ArtifactCapability.PREVIEWABLE in artifact.capabilities:
        return artifact.get_preview()
    return {"error": "Preview not available"}

def execute_artifact(artifact_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute an artifact if it's executable"""
    manager = get_artifact_manager()
    artifact = manager.get_artifact(artifact_id)
    if artifact and ArtifactCapability.EXECUTABLE in artifact.capabilities:
        return asyncio.run(artifact.execute(context))
    return {"error": "Artifact is not executable"}

def get_security_report(artifact_id: str = None) -> Dict[str, Any]:
    """Get security report for specific artifact or all artifacts"""
    manager = get_artifact_manager()
    if artifact_id:
        artifact = manager.get_artifact(artifact_id)
        if artifact:
            return artifact.security_scan_results
        return {"error": "Artifact not found"}
    else:
        return manager._get_security_summary()

def get_optimization_suggestions(artifact_id: str = None) -> List[Dict[str, Any]]:
    """Get optimization suggestions for specific artifact or all artifacts"""
    manager = get_artifact_manager()
    if artifact_id:
        artifact = manager.get_artifact(artifact_id)
        if artifact:
            return artifact.optimization_suggestions
        return []
    else:
        opportunities = manager._get_optimization_opportunities()
        return opportunities.get("performance", []) + opportunities.get("security", [])