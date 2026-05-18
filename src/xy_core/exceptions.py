"""自定义异常层级"""


class XYError(Exception):
    """基础异常"""


class ProjectNotFound(XYError):
    """项目不存在"""


class ProjectAlreadyExists(XYError):
    """项目已存在"""


class InvalidStateTransition(XYError):
    """非法状态流转"""


class ReviewGateError(XYError):
    """评审门操作错误"""


class ArtifactNotReady(XYError):
    """产出物未就绪"""


class AgentConfigError(XYError):
    """Agent配置错误"""


class SkillFormatError(XYError):
    """SKILL.md 格式错误"""
