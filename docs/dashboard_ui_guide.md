# 🍱 Dashboard UI System (Bento Grid)

The Student Hub uses a modern, high-density Bento grid layout designed for maximum information visibility and intuitive workflow.

## 1. Grid Architecture
The dashboard is built on a responsive 4-column CSS grid (`.bento-grid`).

| Section | Span | Priority | Description |
| :--- | :--- | :--- | :--- |
| **Submissions** | `span-1` | High | Active assignment tracking and submission quick-actions. |
| **Project Portfolio** | `span-2` | High | Core project details, mission statement, and update forms. |
| **Activities** | `span-1` | Medium | Live-polling feed of recent team and system events. |
| **Team Members** | `span-2` | Medium | Operational overview of the team with role iconography. |
| **Resources** | `span-1` | Low | Quick access to class documents and materials. |

## 2. Submission-First Logic
The Submissions tile acts as a functional portal rather than a passive timer.

- **Primary Focus**: The most immediate upcoming assignment is featured in a high-contrast `submission-focus-card`.
- **Subtle Countdown**: Real-time countdowns are demoted to corner badges to keep the UI clean.
- **Smart Filling**: If fewer than 4 upcoming milestones exist, the system automatically pulls the most recent **passed** events to fill the vertical space.
- **Direct Bridges**: "Submit Files" buttons on the dashboard trigger the submission modals directly without page reloads.

## 3. Academic Timeline
A centralized modal accessible via the footer of the Submissions tile.

- **Global Search**: Filter all project milestones by title or status in real-time.
- **Status Indicators**: 
    - `Next Up`: The very next deadline.
    - `Passed`: Assignments that have already reached their deadline.
    - `Upcoming`: Future milestones beyond the next one.
- **Submission Integration**: Clicking a timeline row allows students to submit files for that specific assignment immediately.

## 4. Document Preview & File Viewer
The platform features an integrated, high-fidelity document viewer to replace default browser "auto-download" behavior.

- **Unified Modal**: All resource links and submission attachments trigger the `#fileViewerModal` defined in the base template.
- **Supported Formats**:
    - **PDFs & Images**: Rendered natively using browser engines for maximum clarity.
    - **Office Docs**: Rendered via secure Google Docs Viewer integration (DOCX, XLSX, PPTX).
    - **Fallbacks**: Unsupported files display a "Preview Unavailable" screen with a direct download bridge.
- **Persistent Access**: A high-visibility "Download" button is pinned to the viewer header, ensuring users can always save files locally.

## 5. UI Philosophies
- **Aesthetics**: Uses `bg-dark-blue` surfaces with `primary-red` accents for a premium "Command Center" feel.
- **Minimalist Branding**: Removed decorative branding elements (dots) to focus on functional clarity and content.
- **Glassmorphism**: Subtle borders (`border-soft`) and high-contrast cards create depth.
- **Micro-interactions**: Hover states (`transition-all`) provide tactile feedback for interactive elements.
- **Zero-Refresh**: Most actions (Project updates, timeline filtering) are handled via AJAX/JS to maintain state.
