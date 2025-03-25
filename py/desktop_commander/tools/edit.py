from typing import Dict, Tuple
from desktop_commander.types import SearchReplaceBlock
from desktop_commander.tools.filesystem import read_file, write_file


async def perform_search_replace(file_path: str, block: SearchReplaceBlock) -> None:
    """
    Perform a search and replace operation on a file.
    
    Args:
        file_path: Path to the file to edit
        block: Search and replace block defining what to search for and what to replace it with
    """
    content = await read_file(file_path)
    
    # Find first occurrence
    search_index = content.find(block.search)
    if search_index == -1:
        raise Exception(f"Search content not found in {file_path}")
    
    # Replace content
    new_content = (
        content[:search_index] + 
        block.replace + 
        content[search_index + len(block.search):]
    )
    
    await write_file(file_path, new_content)


async def parse_edit_block(block_content: str) -> Tuple[str, SearchReplaceBlock]:
    """
    Parse an edit block into file path and search/replace content.
    
    Format:
    ```
    file_path
    <<<<<<< SEARCH
    search content
    =======
    replace content
    >>>>>>> REPLACE
    ```
    
    Returns:
        Tuple with file path and SearchReplaceBlock
    """
    lines = block_content.split('\n')
    
    # First line should be the file path
    file_path = lines[0].strip()
    
    # Find the markers
    search_start = -1
    divider = -1
    replace_end = -1
    
    for i, line in enumerate(lines):
        if line.strip() == '<<<<<<< SEARCH':
            search_start = i
        elif line.strip() == '=======':
            divider = i
        elif line.strip() == '>>>>>>> REPLACE':
            replace_end = i
    
    if search_start == -1 or divider == -1 or replace_end == -1:
        raise Exception('Invalid edit block format - missing markers')
    
    # Extract search and replace content
    search = '\n'.join(lines[search_start + 1:divider])
    replace = '\n'.join(lines[divider + 1:replace_end])
    
    return file_path, SearchReplaceBlock(search=search, replace=replace)