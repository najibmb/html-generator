import sys
import os
import csv
import json
import html

def read_tracking_csv(file_path):
    """
    Reads the CSV tracking data using the exact column mappings.
    Applies sanity checking and error handling during data ingestion.
    """
    if not os.path.isabs(file_path):
        print(f"Error: The provided path '{file_path}' is not an absolute path.")
        sys.exit(1)
        
    if not os.path.exists(file_path):
        print(f"Error: File does not exist at path: {file_path}")
        sys.exit(1)
        
    expected_headers = ["device_id", "name", "status", "battery_pct", "lat", "lon", "last_seen", "location"]
    parsed_records = []
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            # Check if file is empty
            if os.path.getsize(file_path) == 0:
                print("Error: Input CSV file is empty.")
                sys.exit(1)
                
            reader = csv.DictReader(f)
            
            # Verify the 1st row headers match our arrangement criteria exactly
            if not reader.fieldnames:
                print("Error: CSV file missing header row.")
                sys.exit(1)
                
            # Verify required columns exist
            for header in expected_headers:
                if header not in reader.fieldnames:
                    print(f"Error: Missing required column header field: '{header}'")
                    sys.exit(1)
            
            for row_idx, row in enumerate(reader, start=2):
                # Sanity Check: Ensure no empty critical fields
                try:
                    lat_val = float(row["lat"])
                    lon_val = float(row["lon"])
                except (ValueError, TypeError):
                    print(f"Warning: Skipping row {row_idx} due to invalid or corrupt lat/lon data.")
                    continue
                
                # Geolocation Boundary Check on the 2D plane
                if not (-90 <= lat_val <= 90) or not (-180 <= lon_val <= 180):
                    print(f"Warning: Skipping row {row_idx} because coordinates are out of global bounds.")
                    continue

                # Standardize object fields mimicking the structural keys
                record = {
                    "device_id": row["device_id"].strip(),
                    "name": row["name"].strip(),
                    "status": row["status"].strip().lower(),
                    "battery_pct": row["battery_pct"].strip(),
                    "lat": lat_val,
                    "lon": lon_val,
                    "last_seen": row["last_seen"].strip(),
                    "location": row["location"].strip()
                }
                parsed_records.append(record)
                
    except Exception as e:
        print(f"CRITICAL Error while processing the CSV file: {e}")
        sys.exit(1)
        
    return parsed_records

def generate_html_output(data_records, output_filename="fleet_dashboard.html"):
    """
    Generates a single, standalone static HTML page pre-baked with the coordinates.
    Overwrites any existing dashboard.html file directly on execution.
    """
    # Calculate Fleet Bounding Center Points to initialize map placement cleanly
    if data_records:
        lats = [r["lat"] for r in data_records]
        lons = [r["lon"] for r in data_records]
        center_lat = (max(lats) + min(lats)) / 2.0
        center_lon = (max(lons) + min(lons)) / 2.0
    else:
        center_lat = 0.0
        center_lon = 0.0

    # Serialize data cleanly to standard JSON format embedded directly inside the template
    json_data_array = json.dumps(data_records, indent=2)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fleet Tracking Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background-color: #f5f7fb;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 25px;
        }}
        h1 {{
            margin: 0 0 5px 0;
            color: #1e293b;
            font-size: 28px;
        }}
        p.subtitle {{
            margin: 0;
            color: #64748b;
        }}
        /* SECTION 1: Canvas Wrapper & Controls */
        .map-section {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
            padding: 20px;
            margin-bottom: 30px;
            position: relative;
        }}
        .canvas-container {{
            position: relative;
            width: 100%;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }}
        canvas {{
            display: block;
            cursor: grab;
        }}
        canvas:active {{
            cursor: grabbing;
        }}
        .zoom-controls {{
            position: absolute;
            top: 35px;
            right: 35px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .zoom-btn {{
            width: 40px;
            height: 40px;
            background: white;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-size: 20px;
            font-weight: bold;
            color: #334155;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            justify-content: center;
            user-select: none;
        }}
        .zoom-btn:hover {{
            background: #f1f5f9;
            color: #0f172a;
        }}
        .map-hint {{
            font-size: 12px;
            color: #64748b;
            margin-top: 8px;
            display: block;
        }}
        /* SECTIONS 2 & 3: Layout Components */
        .tables-grid {{
            display: flex;
            flex-direction: column;
            gap: 30px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
            padding: 20px;
        }}
        h2 {{
            margin: 0 0 15px 0;
            color: #1e293b;
            font-size: 20px;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 1px solid #e2e8f0;
        }}
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            font-size: 14px;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        /* Status Color Badges for Table Rows */
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
        }}
        .badge-active {{ background-color: #dcfce7; color: #166534; }}
        .badge-idle {{ background-color: #fef9c3; color: #854d0e; }}
        .badge-offline {{ background-color: #f1f5f9; color: #475569; }}
        .badge-low_battery {{ background-color: #fee2e2; color: #991b1b; }}
        
        .progress-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            max-width: 300px;
        }}
        .progress-bar-bg {{
            background-color: #e2e8f0;
            border-radius: 4px;
            height: 12px;
            flex-grow: 1;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            border-radius: 4px;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Fleet Tracking Dashboard</h1>
        <p class="subtitle">Static summary report generated dynamically from vehicle logs</p>
    </header>

    <section class="map-section">
        <h2>Live Geolocation Coordinates Plane</h2>
        <div class="canvas-container" id="canvas-holder">
            <canvas id="mapCanvas" width="1160" height="500"></canvas>
            <div class="zoom-controls">
                <div class="zoom-btn" id="zoom-in-btn" title="Zoom In">+</div>
                <div class="zoom-btn" id="zoom-out-btn" title="Zoom Out">−</div>
            </div>
        </div>
        <span class="map-hint">💡 Use <strong>Click & Drag</strong> to pan around the map matrix. Hover over diamonds to check device IDs.</span>
    </section>

    <div class="tables-grid">
        <section class="card">
            <h2>Fleet Operational Summary</h2>
            <table id="summaryTable">
                <thead>
                    <tr>
                        <th>Status Key</th>
                        <th>Total Assets</th>
                        <th>Operational Distribution</th>
                    </tr>
                </thead>
                <tbody id="summaryTableBody">
                    </tbody>
            </table>
        </section>

        <section class="card">
            <h2>Device Asset Manifest Logs</h2>
            <table id="deviceTable">
                <thead>
                    <tr>
                        <th>Device ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Battery level</th>
                        <th>Last Seen Status</th>
                        <th>Calculated Location String</th>
                    </tr>
                </thead>
                <tbody id="deviceTableBody">
                    </tbody>
            </table>
        </section>
    </div>
</div>

<script>
    // Embed the payload directly using identical column structures
    const trackingData = {json_data_array};

    // Pre-calculated coordinates from python compiler to automatically center fleet points
    const initialCenterLat = {center_lat};
    const initialCenterLon = {center_lon};

    // Viewport matrix management state tracking variables
    let zoomLevel = 1.0;
    let offsetX = 0;
    let offsetY = 0;
    let hoveredPoint = null;

    // Handles to maintain cursor slide calculations during click dragging
    let isDragging = false;
    let startMouseX = 0;
    let startMouseY = 0;

    const canvas = document.getElementById('mapCanvas');
    const ctx = canvas.getContext('2d');

    // Setup color configuration matrix matching the logic rules
    const STATUS_COLORS = {{
        'active': '#22c55e',      // Green
        'idle': '#eab308',        // Yellow
        'offline': '#64748b',     // Dark Gray
        'low_battery': '#ef4444'  // Red
    }};

    // Initialization lifecycle hook
    window.addEventListener('load', () => {{
        initDashboard();
        centerMapOnCoordinates(initialCenterLat, initialCenterLon);
        renderCanvasMap();
    }});

    function initDashboard() {{
        const manifestBody = document.getElementById('deviceTableBody');
        const summaryBody = document.getElementById('summaryTableBody');
        
        // Accumulator mapping counters matching the operational summaries
        const aggregates = {{ active: 0, idle: 0, offline: 0, low_battery: 0 }};
        
        manifestBody.innerHTML = '';
        
        // Loop through data array natively in a single pass to maintain optimal structure
        trackingData.forEach(item => {{
            // Increment aggregate tracking metrics
            if (item.status in aggregates) {{
                aggregates[item.status]++;
            }} else {{
                aggregates['offline']++; // Fallback sanity check safely
            }}

            // Native formatting logic to parse "how long ago" string relative to current run
            const timePhrase = formatLastSeen(item.last_seen);

            // Populate table row string matching formatting requirements
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${{escapeHtml(item.device_id)}}</strong></td>
                <td>${{escapeHtml(item.name)}}</td>
                <td><span class="badge badge-${{item.status}}">${{escapeHtml(item.status)}}</span></td>
                <td>${{escapeHtml(item.battery_pct)}}%</td>
                <td>${{timePhrase}}</td>
                <td>${{escapeHtml(item.location)}}</td>
            `;
            manifestBody.appendChild(row);
        }});

        // Generate the summary aggregate metric display row calculations
        const totalFleetSize = trackingData.length || 1;
        Object.keys(aggregates).forEach(statusKey => {{
            const count = aggregates[statusKey];
            const percentage = ((count / totalFleetSize) * 100).toFixed(1);
            const hexColor = STATUS_COLORS[statusKey];

            const sRow = document.createElement('tr');
            sRow.innerHTML = `
                <td><span class="badge badge-${{statusKey}}"><strong>${{statusKey}}</strong></span></td>
                <td>${{count}} devices</td>
                <td>
                    <div class="progress-wrapper">
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${{percentage}}%; background-color: ${{hexColor}};"></div>
                        </div>
                        <span style="font-size:12px; color:#64748b; font-weight:500;">${{percentage}}%</span>
                    </div>
                </td>
            `;
            summaryBody.appendChild(sRow);
        }});
    }}

    // Fallback parser to determine a human friendly phrase out of a timeline signature
    function formatLastSeen(isoStr) {{
        if (!isoStr) return "Unknown date";
        try {{
            const targetDate = new Date(isoStr);
            const now = new Date();
            const diffMs = now - targetDate;
            
            if (isNaN(diffMs) || diffMs < 0) {{
                // Fallback phrase if timestamp string represents future context during test
                return "Just now";
            }}
            
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffMins < 1) return "Just now";
            if (diffMins < 60) return `${{diffMins}} minute${{diffMins > 1 ? 's' : ''}} ago`;
            if (diffHours < 24) return `${{diffHours}} hour${{diffHours > 1 ? 's' : ''}} ago`;
            return `${{diffDays}} day${{diffDays > 1 ? 's' : ''}} ago`;
        }} catch (e) {{
            return isoStr;
        }}
    }}

    // Shift screen translation vectors so target fleet geometry balances right in viewport center axis
    function centerMapOnCoordinates(lat, lon) {{
        const normX = (lon + 180) / 360;
        const normY = (90 - lat) / 180;

        const worldX = normX * canvas.width;
        const worldY = normY * canvas.height;

        offsetX = (canvas.width / 2) - (worldX * zoomLevel);
        offsetY = (canvas.height / 2) - (worldY * zoomLevel);
    }}

    // Core Coordinate Projection Geometry Mapping Loop
    function getScreenXY(lat, lon) {{
        // Pure 2D XY plane equation where longitude maps -180 to 180 and latitude maps 90 to -90
        const normX = (lon + 180) / 360;
        const normY = (90 - lat) / 180; // Inverted Y dimension so north is top-side on canvas layout

        // Factor in current state adjustments for the viewport scaling matrix variables
        const screenX = (normX * canvas.width * zoomLevel) + offsetX;
        const screenY = (normY * canvas.height * zoomLevel) + offsetY;
        return {{ x: screenX, y: screenY }};
    }}

    function renderCanvasMap() {{
        // Reset full layout canvas viewport buffer frame
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw helpful grid background indicators across global projection paths
        drawGridLines();

        // Loop through and paint tracking points
        trackingData.forEach(item => {{
            const pos = getScreenXY(item.lat, item.lon);
            const color = STATUS_COLORS[item.status] || '#cbd5e1';
            
            drawDiamond(ctx, pos.x, pos.y, 14, color);
        }});

        // Overlap active hovered text right on top to ensure no pixel data truncation occurs
        if (hoveredPoint && !isDragging) {{
            const pos = getScreenXY(hoveredPoint.lat, hoveredPoint.lon);
            drawTooltip(ctx, hoveredPoint.device_id, pos.x, pos.y);
        }}
    }}

    function drawDiamond(context, cx, cy, size, fillStyle) {{
        context.save();
        context.beginPath();
        context.moveTo(cx, cy - size / 2);      // Top Vertex
        context.lineTo(cx + size / 2, cy);      // Right Vertex
        context.lineTo(cx, cy + size / 2);      // Bottom Vertex
        context.lineTo(cx - size / 2, cy);      // Left Vertex
        context.closePath();
        
        context.fillStyle = fillStyle;
        context.fill();
        context.lineWidth = 1.5;
        context.strokeStyle = '#ffffff';
        context.stroke();
        context.restore();
    }}

    function drawTooltip(context, text, x, y) {{
        context.save();
        context.font = 'bold 11px sans-serif';
        context.textAlign = 'center';
        
        // Offset directly on top of vertex position to resolve tiny clutter layouts
        const textY = y - 12;

        // Draw shadow contrast box behind device ID typography
        const textWidth = context.measureText(text).width;
        context.fillStyle = 'rgba(15, 23, 42, 0.85)';
        context.fillRect(x - (textWidth / 2) - 6, textY - 12, textWidth + 12, 18);
        
        context.fillStyle = '#ffffff';
        context.fillText(text, x, textY);
        context.restore();
    }}

    function drawGridLines() {{
        ctx.save();
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 0.5;
        
        // Horizontal Latitude Reference bounds lines
        for (let l = -60; l <= 60; l += 30) {{
            const pos = getScreenXY(l, 0);
            ctx.beginPath();
            ctx.moveTo(0, pos.y);
            ctx.lineTo(canvas.width, pos.y);
            ctx.stroke();
        }}
        // Vertical Longitude Reference boundaries
        for (let g = -120; g <= 120; g += 60) {{
            const pos = getScreenXY(0, g);
            ctx.beginPath();
            ctx.moveTo(pos.x, 0);
            ctx.lineTo(pos.x, canvas.height);
            ctx.stroke();
        }}
        ctx.restore();
    }}

    // Zoom state machine operations interface listeners
    document.getElementById('zoom-in-btn').addEventListener('click', () => {{
        modifyZoom(1.3);
    }});

    document.getElementById('zoom-out-btn').addEventListener('click', () => {{
        modifyZoom(1 / 1.3);
    }});

    function modifyZoom(multiplier) {{
        const oldZoom = zoomLevel;
        zoomLevel *= multiplier;
        
        // Safety lock clamp bounds to prevent breaking viewport coordinate projection matrix
        if (zoomLevel < 0.3) zoomLevel = 0.3;
        if (zoomLevel > 2500.0) zoomLevel = 2500.0;
        
        // Adjust system layout offset variables dynamically so zoom targets center axis viewport
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        offsetX = centerX - (centerX - offsetX) * (zoomLevel / oldZoom);
        offsetY = centerY - (centerY - offsetY) * (zoomLevel / oldZoom);
        
        renderCanvasMap();
    }}

    // Mouse drag state interaction hooks
    canvas.addEventListener('mousedown', (e) => {{
        isDragging = true;
        const rect = canvas.getBoundingClientRect();
        startMouseX = e.clientX - rect.left;
        startMouseY = e.clientY - rect.top;
    }});

    window.addEventListener('mouseup', () => {{
        if (isDragging) {{
            isDragging = false;
            renderCanvasMap();
        }}
    }});

    // Tooltip Raycasting Engine Event Listeners
    canvas.addEventListener('mousemove', (event) => {{
        const rect = canvas.getBoundingClientRect();
        const currentMouseX = event.clientX - rect.left;
        const currentMouseY = event.clientY - rect.top;
        
        if (isDragging) {{
            // Pull tracking step delta variations
            const dx = currentMouseX - startMouseX;
            const dy = currentMouseY - startMouseY;
            
            // Apply movement translations directly to map viewport position anchors
            offsetX += dx;
            offsetY += dy;
            
            startMouseX = currentMouseX;
            startMouseY = currentMouseY;
            
            renderCanvasMap();
            return;
        }}
        
        let pointFound = null;
        const hitRadius = 10; // Precision collision trigger range in pixels

        // Loop array in reverse matrix order to pull the top layered plot elements first
        for (let i = trackingData.length - 1; i >= 0; i--) {{
            const item = trackingData[i];
            const pos = getScreenXY(item.lat, item.lon);
            
            // Measure strict distance delta calculations
            const dx = currentMouseX - pos.x;
            const dy = currentMouseY - pos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance <= hitRadius) {{
                pointFound = item;
                break;
            }}
        }}

        if (pointFound !== hoveredPoint) {{
            hoveredPoint = pointFound;
            // Switch pointer styles dynamically matching software best practices
            canvas.style.cursor = hoveredPoint ? 'pointer' : 'default';
            renderCanvasMap();
        }}
    }});

    function escapeHtml(str) {{
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }}
</script>

</body>
</html>
"""

    try:
        # Save output document directly, completely overwriting existing outputs
        with open(output_filename, "w", encoding="utf-8") as out_file:
            out_file.write(html_template)
        print(f"Success: Static dashboard compile pipeline execution complete. File saved to: {os.path.abspath(output_filename)}")
    except Exception as e:
        print(f"Error writing compiled HTML asset to disk: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle parameter constraints check execution lifecycle
    if len(sys.argv) != 2:
        print("Usage error: Please provide exactly one absolute file path parameter for the source CSV logging manifest.")
        print("Example: python generate_dashboard.py /Users/admin/data/fleet.csv")
        sys.exit(1)

    csv_path_argument = sys.argv[1]
    
    # Ingest logs
    records = read_tracking_csv(csv_path_argument)
    
    # Compile static single file resource completely decoupled from active streaming loops
    generate_html_output(records)