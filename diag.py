import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Initialize 14x11 widescreen high-resolution canvas
fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 11)
ax.axis('off')

# Design Theme Palette: Academic Blue & Clean Slate
bg_body = '#FFFFFF'
bg_header = '#1E3A8A'  # Deep Academic Navy
border_dark = '#1E293B'
text_white = '#FFFFFF'
text_dark = '#0F172A'
line_color = '#64748B'

def draw_model_table(x, y, w, h, name, columns):
    """Draws a standard database entity class table module with distinct fields."""
    # Main outer card container
    rect_body = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor=border_dark, facecolor=bg_body)
    ax.add_patch(rect_body)
    
    # Class Table Header Segment
    header_h = 0.45
    rect_header = patches.Rectangle((x, y + h - header_h), w, header_h, linewidth=1.5, 
                                    edgecolor=border_dark, facecolor=bg_header)
    ax.add_patch(rect_header)
    
    # Class Title Text (Slightly reduced size to ensure fit)
    ax.text(x + w/2, y + h - (header_h/2), name, fontsize=9, fontweight='bold', 
            color=text_white, ha='center', va='center')
    
    # Populate Entity Attributes line-by-line
    for idx, col in enumerate(columns):
        y_pos = y + h - header_h - 0.22 - (idx * 0.24)
        # Separate constraint tokens, fields, and type annotations
        parts = col.split(' : ')
        field_left = parts[0]
        type_right = parts[1] if len(parts) > 1 else ""
        
        # Draw text columns with safe horizontal offsets to prevent edge overflow
        ax.text(x + 0.12, y_pos, field_left, fontsize=7.5, color=text_dark, ha='left', va='center')
        ax.text(x + w - 0.12, y_pos, type_right, fontsize=7, color='#475569', ha='right', va='center')

# --- DEFINITIONS OF LOGICAL OBJECT ENTITY MATRICES (WIDER BOXES FOR SAFE SPACING) ---
# Column 1 (x=0.4, Width=2.8)
draw_model_table(0.4, 7.8, 2.8, 1.8, "User Class Model", [
    "🔑 id : Integer (PK)",
    "👤 username : String(50)",
    "📧 email : String(120)",
    "🔒 password_hash : String(128)",
    "🎓 role : String(20)"
])

draw_model_table(0.4, 4.8, 2.8, 1.8, "Discussion Model", [
    "🔑 id : Integer (PK)",
    "🔗 course_id : Integer (FK)",
    "🔗 user_id : Integer (FK)",
    "💬 message : Text",
    "📅 timestamp : DateTime",
    "↩️ parent_id : Integer (FK)"
])

# Column 2 (x=3.6, Width=2.8)
draw_model_table(3.6, 8.2, 2.8, 1.4, "Enrollment Model", [
    "🔑 id : Integer (PK)",
    "🔗 user_id : Integer (FK)",
    "🔗 course_id : Integer (FK)",
    "📅 enrolled_at : DateTime",
    "📈 progress : Float"
])

draw_model_table(3.6, 4.8, 2.8, 1.5, "Quiz Class Model", [
    "🔑 id : Integer (PK)",
    "🔗 course_id : Integer (FK)",
    "✏️ title : String(100)",
    "💯 max_score : Integer",
    "⏱️ duration_mins : Integer"
])

draw_model_table(3.6, 1.5, 2.8, 1.6, "Quiz_Attempt Model", [
    "🔑 id : Integer (PK)",
    "🔗 quiz_id : Integer (FK)",
    "🔗 user_id : Integer (FK)",
    "📊 score_obtained : Float",
    "📅 completed_at : DateTime",
    "✅ passed : Boolean"
])

# Column 3 (x=6.8, Width=2.9)
draw_model_table(6.8, 7.6, 2.9, 2.0, "Course Class Model", [
    "🔑 id : Integer (PK)",
    "📚 title : String(100)",
    "📝 description : Text",
    "🔗 instructor_id : Integer (FK)",
    "📅 created_at : DateTime",
    "🏷️ image_file : String(20)"
])

draw_model_table(6.8, 4.8, 2.9, 1.5, "Assignment Model", [
    "🔑 id : Integer (PK)",
    "🔗 course_id : Integer (FK)",
    "📋 title : String(100)",
    "📄 description : Text",
    "📅 due_date : DateTime"
])

draw_model_table(6.8, 1.5, 2.9, 1.6, "Assignment_Submission", [
    "🔑 id : Integer (PK)",
    "🔗 assignment_id : Integer (FK)",
    "🔗 user_id : Integer (FK)",
    "📂 file_path : String(200)",
    "💯 grade : Float",
    "💬 feedback_notes : Text"
])

# Column 4 (x=10.1, Width=2.8)
draw_model_table(10.1, 8.0, 2.8, 1.6, "Lesson Class Model", [
    "🔑 id : Integer (PK)",
    "🔗 course_id : Integer (FK)",
    "📖 title : String(100)",
    "📄 content : Text",
    "🎥 video_url : String(200)",
    "🔢 order_index : Integer"
])

draw_model_table(10.1, 4.8, 2.8, 1.4, "Certificate Model", [
    "🔑 id : Integer (PK)",
    "🔗 user_id : Integer (FK)",
    "🔗 course_id : Integer (FK)",
    "📅 issue_date : DateTime",
    "🛡️ secure_hash : String(64)"
])


# --- CORRELATED RELATIONSHIP CONNECTIONS MAP (UPDATED VECTOR PATHS) ---
def draw_relationship(pts, label_1="1", label_many="*"):
    """Plots multi-point structural mapping paths across schemas."""
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=line_color, linewidth=1.2, linestyle='-')
    # Label indicators positioned safely outside line junctions
    ax.text(xs[0] + 0.06, ys[0] - 0.12, label_1, fontsize=8, fontweight='bold', color='#1E40AF')
    ax.text(xs[-1] - 0.12, ys[-1] + 0.06, label_many, fontsize=9, fontweight='bold', color='#B91C1C')

# User ORM Link Paths
draw_relationship([(1.8, 7.8), (1.8, 2.3), (3.6, 2.3)], "1", "*")      # User -> Quiz_Attempt
draw_relationship([(1.4, 7.8), (1.4, 6.6)], "1", "*")                  # User -> Discussion
draw_relationship([(3.2, 8.7), (3.6, 8.7)], "1", "*")                  # User -> Enrollment

# Course Base Anchor Mappings
draw_relationship([(6.8, 8.6), (6.4, 8.6)], "1", "*")                  # Course -> Enrollment
draw_relationship([(9.7, 8.8), (10.1, 8.8)], "1", "*")                # Course -> Lesson
draw_relationship([(8.25, 7.6), (8.25, 6.3)], "1", "*")                # Course -> Assignment
draw_relationship([(6.8, 7.8), (5.0, 7.8), (5.0, 6.3)], "1", "*")      # Course -> Quiz
draw_relationship([(9.7, 7.6), (11.5, 7.6), (11.5, 6.2)], "1", "*")    # Course -> Certificate

# Core Evaluation Operational Pipes
draw_relationship([(5.0, 4.8), (5.0, 3.1)], "1", "*")                  # Quiz -> Quiz_Attempt
draw_relationship([(8.25, 4.8), (8.25, 3.1)], "1", "*")                # Assignment -> Submission

# Figure Title Header Caption Placement
plt.title("Figure 3.4: Logical Class Model and Object Relationship Map of the SQLAlchemy Schema", 
          y=-0.03, fontsize=11, fontweight='bold', color=border_dark, family='sans-serif')

plt.tight_layout()
plt.savefig('sqlalchemy_class_model.png', bbox_inches='tight', dpi=300)
print("Success! Open 'sqlalchemy_class_model.png' to check your perfect layout.")