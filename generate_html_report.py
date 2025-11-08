"""Generate a comprehensive HTML report with all output fields."""
import asyncio
import json
import html as html_module
from datetime import datetime
from sqlalchemy import select
from src.core.config import get_settings
from src.core.database import init_database, close_database
from src.core.models import SnapshotPath, FileContent
from src.reports.generators import (
    generate_change_report,
    generate_snapshot_report,
    generate_deduplication_report,
)


def format_json_pretty(data):
    """Format data as pretty JSON for textbox display."""
    return json.dumps(data, indent=2, default=str)


def html_escape(text):
    """Escape text for safe HTML display."""
    if text is None:
        return ''
    return html_module.escape(str(text))


async def generate_comprehensive_html():
    """Generate a comprehensive HTML report with all fields."""
    settings = get_settings()
    db = await init_database(settings.database_url, echo=False)

    try:
        async with db.get_session() as session:
            # Generate all reports
            change_report = await generate_change_report(session, snapshot_id=2)
            snapshot_report = await generate_snapshot_report(session, snapshot_id=2)
            dedup_report = await generate_deduplication_report(session)

            # Fetch actual file contents
            stmt = (
                select(SnapshotPath, FileContent)
                .join(FileContent, SnapshotPath.content_id == FileContent.id)
                .where(SnapshotPath.snapshot_id == 2)
                .where(SnapshotPath.exists == True)
                .order_by(SnapshotPath.category, SnapshotPath.name)
            )
            result = await session.execute(stmt)
            file_contents = []
            for path, content in result:
                file_contents.append({
                    'category': path.category,
                    'name': path.name,
                    'path_template': path.path_template,
                    'resolved_path': path.resolved_path,
                    'size_bytes': path.size_bytes,
                    'content_type': content.content_type,
                    'content_text': content.content_text,
                    'modified_time': path.modified_time,
                })

            # Build HTML
            html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Config Reports - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 30px;
        }}

        .section {{
            margin-bottom: 40px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}

        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-size: 1.5em;
            font-weight: bold;
        }}

        .section-body {{
            padding: 20px;
            background: #fafafa;
        }}

        .field {{
            margin-bottom: 20px;
        }}

        .field-label {{
            display: block;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1em;
        }}

        .field-value {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            background: white;
            color: #333;
            resize: vertical;
            min-height: 45px;
            transition: border-color 0.3s;
        }}

        .field-value:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .field-value.large {{
            min-height: 200px;
            font-size: 0.85em;
        }}

        .field-value.medium {{
            min-height: 100px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}

        .stat-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}

        .change-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            margin-bottom: 15px;
        }}

        .change-item.added {{
            border-left-color: #4caf50;
        }}

        .change-item.modified {{
            border-left-color: #ff9800;
        }}

        .change-item.deleted {{
            border-left-color: #f44336;
        }}

        .change-item .path {{
            font-weight: bold;
            font-family: 'Courier New', monospace;
            color: #333;
            margin-bottom: 8px;
        }}

        .change-item .details {{
            font-size: 0.9em;
            color: #666;
        }}

        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 2px solid #e0e0e0;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }}

        .badge.success {{
            background: #4caf50;
            color: white;
        }}

        .badge.warning {{
            background: #ff9800;
            color: white;
        }}

        .badge.danger {{
            background: #f44336;
            color: white;
        }}

        .badge.info {{
            background: #2196f3;
            color: white;
        }}

        /* Search Controls */
        .search-controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border: 2px solid #667eea;
        }}

        .search-row {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}

        .search-input {{
            flex: 1;
            min-width: 300px;
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

        .search-input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .search-button {{
            padding: 10px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1em;
            transition: transform 0.2s;
        }}

        .search-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .filter-group {{
            display: flex;
            gap: 20px;
            align-items: center;
        }}

        .filter-group label {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-weight: 500;
            cursor: pointer;
        }}

        .filter-group input[type="radio"] {{
            cursor: pointer;
        }}

        .filter-select {{
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 0.95em;
            cursor: pointer;
        }}

        .search-results {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}

        .file-container {{
            margin-bottom: 20px;
        }}

        .file-container.hidden {{
            display: none;
        }}

        .highlight {{
            background-color: yellow;
            font-weight: bold;
        }}

        .no-results {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 6px;
            color: #856404;
            text-align: center;
            font-weight: bold;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Claude Config Reports</h1>
            <p>Comprehensive Snapshot Analysis & Change Detection</p>
            <p style="font-size: 0.9em; opacity: 0.8;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="content">
            <!-- Change Detection Report -->
            <div class="section">
                <div class="section-header">
                    🔄 Change Detection Report
                    <span class="badge info">{change_report.total_changes} Changes</span>
                </div>
                <div class="section-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="label">Current Snapshot</div>
                            <div class="value">{change_report.snapshot_id}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Previous Snapshot</div>
                            <div class="value">{change_report.previous_snapshot_id}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Total Changes</div>
                            <div class="value">{change_report.total_changes}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Size Change</div>
                            <div class="value" style="color: {'#4caf50' if change_report.size_change_bytes >= 0 else '#f44336'}">
                                {'+' if change_report.size_change_bytes >= 0 else ''}{change_report.size_change_bytes:,}B
                            </div>
                        </div>
                    </div>

                    <div class="field">
                        <label class="field-label">Snapshot Times</label>
                        <textarea class="field-value" readonly>Current: {change_report.snapshot_time}
Previous: {change_report.previous_snapshot_time}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">
                            Modified Files
                            <span class="badge warning">{len(change_report.modified_files)}</span>
                        </label>
                        <textarea class="field-value large" readonly>{format_json_pretty([{
                            'path': f.path_template,
                            'old_size': f.old_size_bytes,
                            'new_size': f.new_size_bytes,
                            'size_delta': f.size_delta,
                            'old_modified': str(f.old_modified_time),
                            'new_modified': str(f.new_modified_time)
                        } for f in change_report.modified_files])}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">
                            Added Files
                            <span class="badge success">{len(change_report.added_files)}</span>
                        </label>
                        <textarea class="field-value medium" readonly>{format_json_pretty([{
                            'path': f.path_template,
                            'size': f.new_size_bytes,
                            'modified': str(f.new_modified_time)
                        } for f in change_report.added_files]) if change_report.added_files else '[]'}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">
                            Deleted Files
                            <span class="badge danger">{len(change_report.deleted_files)}</span>
                        </label>
                        <textarea class="field-value medium" readonly>{format_json_pretty([{
                            'path': f.path_template,
                            'size': f.old_size_bytes,
                            'last_modified': str(f.old_modified_time)
                        } for f in change_report.deleted_files]) if change_report.deleted_files else '[]'}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">Complete Change Report (JSON)</label>
                        <textarea class="field-value large" readonly>{format_json_pretty(change_report.model_dump())}</textarea>
                    </div>
                </div>
            </div>

            <!-- Snapshot Summary Report -->
            <div class="section">
                <div class="section-header">
                    📸 Snapshot Summary Report
                    <span class="badge info">ID: {snapshot_report.snapshot_id}</span>
                </div>
                <div class="section-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="label">Files Found</div>
                            <div class="value">{snapshot_report.files_found}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Directories</div>
                            <div class="value">{snapshot_report.directories_found}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Total Size</div>
                            <div class="value">{snapshot_report.total_size_bytes:,}B</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Deduplication</div>
                            <div class="value">{snapshot_report.deduplication_percent:.1f}%</div>
                        </div>
                    </div>

                    <div class="field">
                        <label class="field-label">Snapshot ID</label>
                        <input type="text" class="field-value" value="{snapshot_report.snapshot_id}" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Snapshot Time</label>
                        <input type="text" class="field-value" value="{snapshot_report.snapshot_time}" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Snapshot Hash</label>
                        <input type="text" class="field-value" value="{snapshot_report.snapshot_hash}" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Trigger Type</label>
                        <input type="text" class="field-value" value="{snapshot_report.trigger_type} (by {snapshot_report.triggered_by or 'N/A'})" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">System Info</label>
                        <textarea class="field-value" readonly>OS: {snapshot_report.os_type}
Hostname: {snapshot_report.hostname or 'N/A'}
Username: {snapshot_report.username or 'N/A'}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">Notes</label>
                        <textarea class="field-value" readonly>{snapshot_report.notes or 'No notes provided'}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">Category Statistics</label>
                        <textarea class="field-value large" readonly>{format_json_pretty([{
                            'category': c.category,
                            'total_locations': c.total_locations,
                            'found': c.found,
                            'missing': c.missing,
                            'total_size_bytes': c.total_size_bytes
                        } for c in snapshot_report.category_stats])}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">All Paths ({len(snapshot_report.paths)} locations)</label>
                        <textarea class="field-value large" readonly>{format_json_pretty([{
                            'category': p.category,
                            'name': p.name,
                            'path_template': p.path_template,
                            'exists': p.exists,
                            'type': p.type,
                            'size_bytes': p.size_bytes
                        } for p in snapshot_report.paths])}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">Complete Snapshot Report (JSON)</label>
                        <textarea class="field-value large" readonly>{format_json_pretty(snapshot_report.model_dump())}</textarea>
                    </div>
                </div>
            </div>

            <!-- Deduplication Report -->
            <div class="section">
                <div class="section-header">
                    💾 Deduplication Statistics
                    <span class="badge success">{dedup_report.savings_percent:.1f}% Saved</span>
                </div>
                <div class="section-body">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="label">Total File Contents</div>
                            <div class="value">{dedup_report.total_file_contents}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Unique Hashes</div>
                            <div class="value">{dedup_report.unique_hashes}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Storage Used</div>
                            <div class="value">{dedup_report.total_size_bytes:,}B</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Savings</div>
                            <div class="value" style="color: #4caf50">{dedup_report.savings_bytes:,}B</div>
                        </div>
                    </div>

                    <div class="field">
                        <label class="field-label">Total References</label>
                        <input type="text" class="field-value" value="{dedup_report.total_references}" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Without Deduplication</label>
                        <input type="text" class="field-value" value="{dedup_report.deduplicated_size_bytes:,} bytes" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Savings Percentage</label>
                        <input type="text" class="field-value" value="{dedup_report.savings_percent:.2f}%" readonly>
                    </div>

                    <div class="field">
                        <label class="field-label">Most Referenced Files</label>
                        <textarea class="field-value large" readonly>{format_json_pretty(dedup_report.most_referenced)}</textarea>
                    </div>

                    <div class="field">
                        <label class="field-label">Complete Deduplication Report (JSON)</label>
                        <textarea class="field-value large" readonly>{format_json_pretty(dedup_report.model_dump())}</textarea>
                    </div>
                </div>
            </div>

            <!-- File Contents Section -->
            <div class="section">
                <div class="section-header">
                    📄 Actual File Contents
                    <span class="badge info">{len(file_contents)} Files</span>
                </div>
                <div class="section-body">
                    <p style="margin-bottom: 20px; color: #666;">
                        Below are the actual contents of each file captured in Snapshot 2.
                        Each file is displayed in its own labeled textbox for easy viewing and copying.
                    </p>

                    <!-- Search Controls -->
                    <div class="search-controls">
                        <div class="search-row">
                            <input type="text" id="searchInput" class="search-input" placeholder="Search file contents...">
                            <button onclick="performSearch()" class="search-button">🔍 Search</button>
                            <button onclick="clearSearch()" class="search-button" style="background: #6c757d;">Clear</button>
                        </div>
                        <div class="search-row">
                            <div class="filter-group">
                                <strong>Search Scope:</strong>
                                <label>
                                    <input type="radio" name="searchScope" value="current" id="scopeCurrent">
                                    Current File Only
                                </label>
                                <label>
                                    <input type="radio" name="searchScope" value="all" id="scopeAll" checked>
                                    All Files
                                </label>
                            </div>
                            <div class="filter-group">
                                <strong>File Type:</strong>
                                <select id="fileTypeFilter" class="filter-select" onchange="filterByFileType()">
                                    <option value="all">All Types</option>
                                    <option value=".json">JSON (.json)</option>
                                    <option value=".md">Markdown (.md)</option>
                                </select>
                            </div>
                        </div>
                        <div id="searchResults" class="search-results"></div>
                        <div id="noResults" class="no-results">No matches found</div>
                    </div>
"""

            # Add each file's content
            for idx, fc in enumerate(file_contents):
                file_size_str = f"{fc['size_bytes']:,} bytes" if fc['size_bytes'] else "0 bytes"
                modified_str = fc['modified_time'].strftime('%Y-%m-%d %H:%M:%S') if fc['modified_time'] else 'N/A'

                # Escape content for safe HTML display
                content_display = html_escape(fc['content_text']) if fc['content_text'] else '(Binary or empty content)'

                # Extract file extension for filtering
                path_template = fc['path_template']
                file_extension = ''
                if path_template:
                    if path_template.endswith('.json'):
                        file_extension = '.json'
                    elif path_template.endswith('.md'):
                        file_extension = '.md'
                    else:
                        # Check for other extensions
                        parts = path_template.split('.')
                        if len(parts) > 1:
                            file_extension = f".{parts[-1]}"

                html += f"""
                    <div class="file-container" id="file-{idx}" data-file-type="{file_extension}" data-file-name="{html_escape(fc['name'])}">
                        <div class="field">
                            <label class="field-label">
                                {html_escape(fc['category'])} → {html_escape(fc['name'])}
                                <span class="badge info">{file_size_str}</span>
                            </label>
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">
                                <strong>Path:</strong> {html_escape(fc['path_template'])}<br>
                                <strong>Resolved:</strong> {html_escape(fc['resolved_path'])}<br>
                                <strong>Type:</strong> {html_escape(fc['content_type'])} |
                                <strong>Modified:</strong> {modified_str}
                            </div>
                            <textarea class="field-value large file-content" id="content-{idx}" readonly>{content_display}</textarea>
                        </div>
                    </div>
"""

            html += """
                </div>
            </div>
        </div>

        <div class="footer">
            <p><strong>Claude Config Version Control System</strong></p>
            <p>Production-grade snapshot management with git-like version control</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Report generated by Claude Config Editor v2.0</p>
        </div>
    </div>

    <script>
        let currentFocusedFile = null;
        let originalContents = new Map();

        // Store original content for each textarea
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.file-content').forEach(textarea => {
                originalContents.set(textarea.id, textarea.value);
            });

            // Track which file is currently focused
            document.querySelectorAll('.file-content').forEach(textarea => {
                textarea.addEventListener('focus', function() {
                    currentFocusedFile = this.id;
                });
            });

            // Allow Enter key to trigger search
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        });

        function performSearch() {
            const searchTerm = document.getElementById('searchInput').value;
            const searchScope = document.querySelector('input[name="searchScope"]:checked').value;
            const fileTypeFilter = document.getElementById('fileTypeFilter').value;
            const resultsDiv = document.getElementById('searchResults');
            const noResultsDiv = document.getElementById('noResults');

            // Clear previous results
            clearHighlights();
            noResultsDiv.style.display = 'none';
            resultsDiv.textContent = '';

            if (!searchTerm.trim()) {
                resultsDiv.textContent = 'Please enter a search term';
                return;
            }

            let totalMatches = 0;
            let filesWithMatches = 0;
            const containers = document.querySelectorAll('.file-container');

            // Determine which files to search
            let filesToSearch = [];
            if (searchScope === 'current' && currentFocusedFile) {
                const fileIdx = currentFocusedFile.replace('content-', '');
                const container = document.getElementById('file-' + fileIdx);
                if (container) {
                    filesToSearch = [container];
                }
            } else {
                filesToSearch = Array.from(containers);
            }

            // Apply file type filter
            if (fileTypeFilter !== 'all') {
                filesToSearch = filesToSearch.filter(container =>
                    container.getAttribute('data-file-type') === fileTypeFilter
                );
            }

            // Search in each file
            filesToSearch.forEach(container => {
                const textarea = container.querySelector('.file-content');
                const originalText = originalContents.get(textarea.id);

                if (!originalText) return;

                // Case-insensitive search
                const regex = new RegExp(escapeRegex(searchTerm), 'gi');
                const matches = originalText.match(regex);

                if (matches && matches.length > 0) {
                    filesWithMatches++;
                    totalMatches += matches.length;

                    // Highlight matches in textarea
                    const highlightedText = originalText.replace(regex, match => `<<<HIGHLIGHT>>>${match}<<<ENDHIGHLIGHT>>>`);
                    textarea.value = highlightedText;

                    // Show the container
                    container.classList.remove('hidden');
                } else {
                    // Hide containers without matches in "all files" mode
                    if (searchScope === 'all') {
                        container.classList.add('hidden');
                    }
                }
            });

            // Show results
            if (totalMatches > 0) {
                resultsDiv.textContent = `Found ${totalMatches} match${totalMatches !== 1 ? 'es' : ''} in ${filesWithMatches} file${filesWithMatches !== 1 ? 's' : ''}`;

                // Scroll to first visible file
                const firstVisible = document.querySelector('.file-container:not(.hidden)');
                if (firstVisible) {
                    firstVisible.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } else {
                noResultsDiv.style.display = 'block';
                resultsDiv.textContent = 'No matches found';
            }
        }

        function clearSearch() {
            // Clear search input
            document.getElementById('searchInput').value = '';

            // Clear results
            document.getElementById('searchResults').textContent = '';
            document.getElementById('noResults').style.display = 'none';

            // Clear highlights and show all files
            clearHighlights();

            // Show all file containers
            document.querySelectorAll('.file-container').forEach(container => {
                container.classList.remove('hidden');
            });

            // Reset file type filter
            document.getElementById('fileTypeFilter').value = 'all';
        }

        function clearHighlights() {
            document.querySelectorAll('.file-content').forEach(textarea => {
                const originalText = originalContents.get(textarea.id);
                if (originalText) {
                    textarea.value = originalText;
                }
            });
        }

        function filterByFileType() {
            const fileType = document.getElementById('fileTypeFilter').value;
            const containers = document.querySelectorAll('.file-container');

            containers.forEach(container => {
                if (fileType === 'all' || container.getAttribute('data-file-type') === fileType) {
                    container.classList.remove('hidden');
                } else {
                    container.classList.add('hidden');
                }
            });

            // Update results count
            const visibleCount = document.querySelectorAll('.file-container:not(.hidden)').length;
            const resultsDiv = document.getElementById('searchResults');

            if (fileType === 'all') {
                resultsDiv.textContent = '';
            } else {
                resultsDiv.textContent = `Showing ${visibleCount} ${fileType} file${visibleCount !== 1 ? 's' : ''}`;
            }
        }

        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        }
    </script>
</body>
</html>
"""

            # Save HTML file
            with open("comprehensive_report.html", "w", encoding="utf-8") as f:
                f.write(html)

            print("SUCCESS: Comprehensive HTML report generated!")
            print("File: comprehensive_report.html")
            print(f"\nReport includes:")
            print(f"  - Change Detection: {change_report.total_changes} changes")
            print(f"  - Snapshot Summary: {snapshot_report.files_found} files, {snapshot_report.directories_found} dirs")
            print(f"  - Deduplication: {dedup_report.savings_percent:.1f}% savings")
            print(f"  - Actual File Contents: {len(file_contents)} files with full text")

    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(generate_comprehensive_html())
