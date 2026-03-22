"""
搜索引擎模块
提供全文搜索和关键词高亮功能
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..shared.models import ClipboardRecord, SearchResult
from ..storage.repository import ClipboardRepository
from ..shared.utils import highlight_text


@dataclass
class SearchOptions:
    """搜索选项"""
    keyword: str = ""
    filter_type: int = 0  # 0 = 全部
    case_sensitive: bool = False
    limit: int = 100


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self, repository: Optional[ClipboardRepository] = None):
        self.repository = repository or ClipboardRepository()
    
    def search(self, options: SearchOptions) -> List[SearchResult]:
        """执行搜索"""
        keyword = options.keyword.strip()
        
        if not keyword:
            # 无关键词，返回所有记录
            records = self.repository.get_all(
                filter_type=options.filter_type,
                limit=options.limit
            )
            return [SearchResult(record=record) for record in records]
        
        # 使用仓库的搜索功能
        records = self.repository.search(
            keyword=keyword,
            filter_type=options.filter_type,
            limit=options.limit
        )
        
        # 计算匹配位置和相关度
        results = []
        for record in records:
            match_positions = self._find_matches(record, keyword, options.case_sensitive)
            relevance = self._calculate_relevance(record, keyword, match_positions)
            
            results.append(SearchResult(
                record=record,
                match_positions=match_positions,
                relevance_score=relevance
            ))
        
        # 按相关度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results
    
    def _find_matches(self, record: ClipboardRecord, keyword: str, 
                      case_sensitive: bool) -> List[Tuple[int, int]]:
        """查找匹配位置"""
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(keyword)
        
        # 在文本内容中查找
        if record.content_type == ClipboardType.TEXT and record.text_content:
            for match in re.finditer(pattern, record.text_content, flags):
                matches.append((match.start(), match.end()))
        
        # 在文件路径中查找
        elif record.content_type == ClipboardType.FILE and record.file_paths:
            offset = 0
            for path in record.file_paths:
                for match in re.finditer(pattern, path, flags):
                    matches.append((offset + match.start(), offset + match.end()))
                offset += len(path) + 1  # +1 for separator
        
        return matches
    
    def _calculate_relevance(self, record: ClipboardRecord, keyword: str,
                            match_positions: List[Tuple[int, int]]) -> float:
        """计算相关度分数"""
        if not match_positions:
            return 0.0
        
        score = 0.0
        
        # 匹配数量加分
        score += len(match_positions) * 10
        
        # 置顶和收藏加分
        if record.is_pinned:
            score += 100
        if record.is_favorite:
            score += 50
        
        # 完整匹配加分
        if record.content_type == ClipboardType.TEXT and record.text_content:
            if keyword.lower() == record.text_content.lower():
                score += 200
        
        # 时间衰减（越新的记录分数越高）
        from datetime import datetime
        age_hours = (datetime.now() - record.created_at).total_seconds() / 3600
        if age_hours < 24:
            score += 30
        elif age_hours < 168:  # 一周
            score += 10
        
        return score
    
    def get_highlighted_content(self, record: ClipboardRecord, keyword: str,
                                max_length: int = 200) -> str:
        """获取高亮显示的内容"""
        if not keyword:
            content = self._get_display_content(record)
            return content[:max_length] + "..." if len(content) > max_length else content
        
        content = self._get_display_content(record)
        highlighted, _ = highlight_text(content, keyword)
        
        # 截断并添加省略号
        if len(content) > max_length:
            # 尝试找到关键词附近的上下文
            keyword_pos = content.lower().find(keyword.lower())
            if keyword_pos >= 0:
                start = max(0, keyword_pos - max_length // 2)
                end = min(len(content), start + max_length)
                snippet = content[start:end]
                
                # 重新高亮截断后的内容
                highlighted, _ = highlight_text(snippet, keyword)
                
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(content) else ""
                return prefix + highlighted + suffix
            else:
                return highlighted[:max_length] + "..."
        
        return highlighted
    
    def _get_display_content(self, record: ClipboardRecord) -> str:
        """获取用于显示的原始内容"""
        if record.content_type == ClipboardType.TEXT:
            return record.text_content or ""
        elif record.content_type == ClipboardType.FILE:
            return "\n".join(record.file_paths) if record.file_paths else ""
        return ""
    
    def quick_search(self, keyword: str, filter_type: int = 0, limit: int = 100) -> List[ClipboardRecord]:
        """快速搜索，返回记录列表"""
        options = SearchOptions(
            keyword=keyword,
            filter_type=filter_type,
            limit=limit
        )
        results = self.search(options)
        return [result.record for result in results]


# 导入 ClipboardType
from ..shared.constants import ClipboardType
