import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from pathlib import Path

@dataclass
class RawBlock:
    block_type: str  # "heading", "paragraph", "list", "table", "yaml_frontmatter"
    raw_content: str
    line_start: int
    line_end: int
    heading_level: Optional[int] = None
    file_path: str = ""

@dataclass
class ParsedMarkdown:
    file_path: str
    blocks: List[RawBlock]
    urls: List[str]
    frontmatter: Dict[str, str]

class MarkdownParser:
    def __init__(self):
        self.heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
        self.table_row_re = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")
        self.url_re = re.compile(r"https?://[^\s)\]>]+")
        self.frontmatter_re = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
        
    def _extract_frontmatter(self, text: str) -> Tuple[Dict[str, str], int]:
        match = self.frontmatter_re.match(text)
        if not match:
            return {}, 0
        fm_text = match.group(1)
        lines = fm_text.splitlines()
        metadata = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip()
        lines_consumed = len(text[:match.end()].splitlines())
        return metadata, lines_consumed

    def _extract_urls(self, text: str) -> List[str]:
        return [match.group(0).rstrip(".,;:)") for match in self.url_re.finditer(text)]

    def parse(self, text: str, file_path: str) -> ParsedMarkdown:
        metadata, start_idx = self._extract_frontmatter(text)
        
        lines = text.splitlines()
        blocks = []
        urls = self._extract_urls(text)
        
        current_block_lines = []
        current_block_type = "paragraph"
        current_start_line = start_idx
        
        def push_block(end_line):
            nonlocal current_block_lines, current_block_type, current_start_line
            if not current_block_lines:
                return
            content = "\n".join(current_block_lines)
            if not content.strip():
                current_block_lines = []
                return
            
            blocks.append(RawBlock(
                block_type=current_block_type,
                raw_content=content,
                line_start=current_start_line,
                line_end=end_line,
                file_path=file_path
            ))
            current_block_lines = []
        
        idx = start_idx
        while idx < len(lines):
            line = lines[idx]
            heading_match = self.heading_re.match(line)
            
            if heading_match:
                push_block(idx)
                blocks.append(RawBlock(
                    block_type="heading",
                    raw_content=line,
                    line_start=idx + 1,
                    line_end=idx + 1,
                    heading_level=len(heading_match.group(1)),
                    file_path=file_path
                ))
                current_start_line = idx + 1
            elif self.table_row_re.match(line):
                if current_block_type != "table":
                    push_block(idx)
                    current_block_type = "table"
                    current_start_line = idx + 1
                current_block_lines.append(line)
            elif line.strip().startswith(("- ", "* ", "1. ")):
                if current_block_type != "list":
                    push_block(idx)
                    current_block_type = "list"
                    current_start_line = idx + 1
                current_block_lines.append(line)
            elif not line.strip():
                push_block(idx)
                current_block_type = "paragraph"
                current_start_line = idx + 2
            else:
                if current_block_type not in ["paragraph", "table", "list"]:
                    current_block_type = "paragraph"
                    current_start_line = idx + 1
                current_block_lines.append(line)
                
            idx += 1
            
        push_block(idx)
        return ParsedMarkdown(file_path=file_path, blocks=blocks, urls=urls, frontmatter=metadata)
