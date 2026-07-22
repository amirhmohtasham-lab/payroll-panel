from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
from pathlib import Path

OUT = Path(__file__).with_name('UAT_TEST_PLAN.pdf')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=27, leading=33, textColor=HexColor('#16324F'), alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name='CoverSub', parent=styles['Normal'], fontSize=13, leading=19, textColor=HexColor('#4A6176'), alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name='H1x', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=17, leading=22, textColor=HexColor('#16324F'), spaceBefore=10, spaceAfter=10))
styles.add(ParagraphStyle(name='H2x', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=HexColor('#0B6E69'), spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name='Bodyx', parent=styles['BodyText'], fontSize=9, leading=13, spaceAfter=6, textColor=HexColor('#243746')))
styles.add(ParagraphStyle(name='Smallx', parent=styles['BodyText'], fontSize=7.5, leading=10, textColor=HexColor('#243746')))
styles.add(ParagraphStyle(name='Cellx', parent=styles['BodyText'], fontSize=7.2, leading=9.2, textColor=HexColor('#243746')))
styles.add(ParagraphStyle(name='CellBold', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=7.4, leading=9.5, textColor=HexColor('#16324F')))

def P(text, style='Bodyx'): return Paragraph(text, styles[style])
def cell(text, bold=False): return P(str(text).replace('\n','<br/>'), 'CellBold' if bold else 'Cellx')

def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(HexColor('#D9E2EC')); canvas.line(0.55*inch,0.48*inch,7.95*inch,0.48*inch)
    canvas.setFont('Helvetica',7); canvas.setFillColor(HexColor('#66788A')); canvas.drawString(0.58*inch,0.3*inch,'Payroll Panel - User Acceptance Testing Plan')
    canvas.drawRightString(7.92*inch,0.3*inch,f'Page {doc.page}'); canvas.restoreState()

def test_table(cases):
    headers=['ID / Title','Preconditions','Steps','Expected Result','Actual Result / Pass-Fail / Tester / Date']
    data=[[cell(h,True) for h in headers]]
    for c in cases:
        data.append([cell(f"<b>{c[0]}</b><br/>{c[1]}"), cell(c[2]), cell(c[3]), cell(c[4]), cell('')])
    t=Table(data,colWidths=[1.05*inch,1.28*inch,2.05*inch,1.75*inch,1.27*inch],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#16324F')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.35,HexColor('#B8C7D6')),('BACKGROUND',(0,1),(-1,-1),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#F4F8FB')]),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t

sections=[
('1. Authentication and Access Control',[
('AUTH-01','Successful login','Application is available; valid operator or accountant test account exists.','Open login page; enter valid username and password; submit.','Login succeeds; session cookie is created; operator lands on /operator and accountant lands on dashboard /.'),
('AUTH-02','Login failure - wrong password','Known username; incorrect password.','Enter username with wrong password; submit.','Login is rejected with a clear error; no protected page is shown; no authenticated session is established.'),
('AUTH-03','Logout','Authenticated session.','Click logout; then navigate to a protected URL.','Session is invalidated, cookie removed, and user is redirected to /login.'),
('AUTH-04','Session expiry and protected-route redirect','Authenticated session that has expired or is manually invalidated.','Open or reload a protected page after expiry.','ProtectedRoute detects missing/expired identity and redirects to /login without exposing protected data.'),
('AUTH-05','Role-based route access','Valid operator and accountant accounts.','As operator, attempt /, /reports, /chat, /fertilizer, /users; as accountant, attempt /operator.','Each role is redirected to its permitted landing page; forbidden screens/API actions are inaccessible.'),
]),
('2. Operator - Payroll Upload',[
('PAY-01','Upload valid payroll .xlsx','Authenticated operator; valid payroll workbook; target month not previously uploaded.','Open operator upload hub; select Payroll; choose month; select .xlsx; click review/upload.','Upload completes; audit runs; success status shows error and warning counts; record and audit detail appear.'),
('PAY-02','Reject non-.xlsx file','Authenticated operator; PDF/CSV/TXT file.','Select non-.xlsx file and submit.','Upload is rejected with a file-type validation message; no upload record is created.'),
('PAY-03','Duplicate month handling','A payroll upload already exists for target month; replacement workbook available.','Upload another workbook for same month; observe duplicate dialog; cancel; repeat and confirm replace.','First attempt is blocked with existing-file details. Cancel leaves original intact. Confirm replace updates the month record and audit results.'),
('PAY-04','Duplicate file hash detection','A payroll workbook already exists under another month.','Upload the identical workbook for a different month.','System detects same SHA-256 content and blocks it with duplicate-file information; no second record is created.'),
('PAY-05','View audit results and download highlighted workbook','Completed payroll upload with at least one error/warning.','Review upload detail; inspect grouped issues; click highlighted-workbook download.','Issues show severity, code/sheet/message and counts; downloaded .xlsx opens and contains highlighted audit findings.'),
]),
('3. Operator - Fertilizer Upload',[
('FERT-01','Upload valid fertilizer .xlsx','Authenticated operator; valid fertilizer workbook; unused month; crop and season known.','Select Fertilizer; select month and crop; enter season; choose .xlsx; submit.','Upload succeeds; row/fertilizer counts and audit counts are shown; crop and season are retained.'),
('FERT-02','Reject non-.xlsx file','Authenticated operator; non-Excel file.','Select PDF/CSV/TXT and submit fertilizer upload.','System rejects the file and does not persist an upload.'),
('FERT-03','Duplicate fertilizer month handling','Fertilizer record exists for selected month.','Submit a new file for same month; cancel replacement; repeat and confirm replacement.','Duplicate dialog identifies existing record. Cancel preserves it; confirmation replaces it and refreshes details.'),
('FERT-04','Duplicate fertilizer file detection','Identical fertilizer workbook exists for another month.','Upload same workbook under another month.','Same-content duplicate is detected and blocked; existing month/file information is displayed.'),
('FERT-05','Fertilizer audit detail and highlighted download','Completed fertilizer upload.','Inspect result details and click highlighted download.','Audit errors/warnings, crop, season, row count and fertilizer count render correctly; highlighted .xlsx downloads successfully.'),
]),
('4. Accountant - Dashboard and Archive',[
('ACCT-01','Dashboard summary cards','Authenticated accountant; payroll data exists.','Open dashboard /; wait for data load.','Cards show registered months, active errors, warnings, and worker count; values match source uploads.'),
('ACCT-02','Dashboard upload hub visibility','Authenticated accountant.','Use Payroll and Fertilizer tabs in Upload Hub; upload a permitted workbook if test data allows.','Both module choices are visible and functional; successful upload refreshes dashboard summary.'),
('ARCH-01','Unified archive list','Authenticated accountant; payroll and fertilizer records exist.','Open Archive.','Single list contains both upload types, labels, error/warning counts and upload timestamps; totals are accurate.'),
('ARCH-02','Archive filtering and detail viewing','Archive contains multiple records.','Use available list navigation/selection; open payroll and fertilizer details.','Selected record opens the correct detail view, preserving month/type context and displaying audit metadata.'),
]),
('5. Accountant - Reports',[
('REP-01','Foreman totals report','Accountant; payroll data with foremen.','Open Reports; select Foreman totals tile.','Table and bar chart render; foreman labels and totals are readable and consistent.'),
('REP-02','Well/location totals report','Accountant; payroll data with workplace/well values.','Select Well/location totals tile.','Table and doughnut chart render; categories and values are present and correctly ranked/limited.'),
('REP-03','Monthly trend report','Accountant; payroll data across months.','Select Monthly trend tile.','Table and chart render month labels with worker receipts and expenses for each month.'),
('REP-04','Status summary report','Accountant; uploads with clean, warning, and error outcomes.','Select Status summary tile.','Table and doughnut chart show clean, warning, and error counts matching audit status.'),
('REP-05','Top 5 foremen report','Accountant; at least five foreman aggregates or available data.','Select Top 5 foremen tile.','Table lists no more than five ranked foremen; bar chart matches table values.'),
('REP-06','General statistics report','Accountant; payroll data exists.','Select General statistics tile.','Table renders month count, sheet count, worker count, and foreman count without errors.'),
]),
('6. Accountant - Chat Assistant',[
('CHAT-01','Send report request and receive chart','Authenticated accountant; report data exists.','Open Chat; send a natural-language report request; wait for response.','User message appears; assistant reply is returned; when applicable an embedded chart/table renders without layout or script errors.'),
('CHAT-02','Chat history persistence across reload','At least one successful chat exchange.','Reload Chat page or navigate away and return.','History endpoint repopulates prior user and assistant messages, including chart content where present.'),
]),
('7. Accountant - User Management',[
('USER-01','Create user','Authenticated accountant; unique username and valid password of at least six characters.','Open Users; enter username, display name, password and role; submit.','User is created, success message appears, and new user appears in list with correct role.'),
('USER-02','List users','Authenticated accountant; users exist.','Open Users page and refresh.','User table loads username, display name and role for all active records.'),
('USER-03','Delete user','Authenticated accountant; disposable test user exists.','Click Delete; confirm prompt.','User is removed from list and subsequent list/API request no longer includes the user.'),
('USER-04','User-management RBAC enforcement','Authenticated operator account.','Navigate to /users and call user-management actions if possible.','Operator cannot view/manage users; UI redirects and API returns authorization failure; no mutation occurs.'),
])]

story=[Spacer(1,0.7*inch),P('PAYROLL PANEL','CoverTitle'),P('User Acceptance Testing Plan','CoverTitle'),P('Release validation for payroll and fertilizer audit workflows','CoverSub'),Spacer(1,0.25*inch)]
cover_data=[[P('<b>Document owner</b>','Smallx'),P('Business / QA Team','Smallx')],[P('<b>Version</b>','Smallx'),P('1.0','Smallx')],[P('<b>Application</b>','Smallx'),P('Payroll Panel','Smallx')],[P('<b>Prepared</b>','Smallx'),P('22 July 2026','Smallx')]]
ct=Table(cover_data,colWidths=[1.6*inch,3.7*inch]);ct.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),HexColor('#E8F1F5')),('GRID',(0,0),(-1,-1),0.35,HexColor('#CBD8E2')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('PADDING',(0,0),(-1,-1),9)]));story += [ct,Spacer(1,0.35*inch),P('This plan provides business-facing scenarios and sign-off evidence for the Persian/RTL Payroll Panel, covering operator ingestion and audit of payroll/fertilizer workbooks and accountant review, reporting, chat, and user administration.', 'CoverSub'),PageBreak()]
story += [P('1. Purpose, Scope and Application Overview','H1x'),P('<b>Purpose.</b> Confirm that the released application supports the end-to-end business workflows expected by operators and accountants, with accurate audit outcomes, secure role separation, usable reporting, and recoverable user interactions.'),P('<b>Scope.</b> Web UI and supporting API behavior for authentication, protected routes, payroll and fertilizer workbook ingestion, duplicate controls, audit issue presentation, highlighted-workbook download, dashboard, archive, reports, chat assistant, and user management. This is a UAT plan, not a replacement for unit, integration, performance, or security testing.'),P('<b>Application overview.</b> Payroll Panel is a Persian/RTL panel with two roles. Operators upload and audit payroll (workforce) and fertilizer consumption workbooks. Accountants review the upload hub, unified archive, audit details, charts/tables, chat-based report assistant, and users. Uploaded workbooks are hashed, persisted, audited, and may be backed up to Google Drive.'),P('2. Environment and Prerequisites','H1x')]
env=[[cell('Item',True),cell('UAT value / requirement',True)],[cell('Test URL',True),cell('Record the deployed URL here: __________________________________________')],[cell('Operator account',True),cell('Username: ____________________  Password: ____________________')],[cell('Accountant account',True),cell('Username: ____________________  Password: ____________________')],[cell('Browser',True),cell('Current Chrome, Edge, or Firefox; clear cookies between role tests when needed.')],[cell('Test data',True),cell('Valid payroll and fertilizer .xlsx files; invalid non-.xlsx file; duplicate-month and same-hash fixtures; records spanning multiple months and audit statuses.')],[cell('Services',True),cell('Application, database, storage, and optional Google Drive backup available. Seed accounts created through environment variables before UAT.')]]
et=Table(env,colWidths=[1.45*inch,5.9*inch]);et.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#0B6E69')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.35,HexColor('#B8C7D6')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor('#F4F8FB')]),('PADDING',(0,0),(-1,-1),6)]));story += [et,PageBreak()]
for title,cases in sections:
    story += [P(title,'H1x'),test_table(cases),Spacer(1,0.12*inch)]
    if title.startswith('3.') or title.startswith('5.') or title.startswith('7.'):
        story.append(PageBreak())
story += [PageBreak(),P('8. Final UAT Sign-off','H1x'),P('Complete this section after all applicable test cases have been executed and evidence has been reviewed.'),Spacer(1,0.1*inch)]
sign=[[cell('Sign-off field',True),cell('Entry',True)],[cell('Tester name'),cell('')],[cell('Business owner / approver'),cell('')],[cell('Execution date'),cell('')],[cell('Overall result'),cell('PASS / FAIL (circle one)')],[cell('Open defects / deviations'),cell('')],[cell('Notes and evidence references'),cell('')],[cell('Tester signature'),cell('')],[cell('Approver signature'),cell('')]]
st=Table(sign,colWidths=[2.15*inch,5.2*inch],rowHeights=[0.28*inch,0.42*inch,0.42*inch,0.42*inch,0.42*inch,0.7*inch,0.9*inch,0.42*inch,0.42*inch]);st.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#16324F')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.4,HexColor('#B8C7D6')),('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,1),(0,-1),HexColor('#E8F1F5')),('PADDING',(0,0),(-1,-1),7)]));story += [st,Spacer(1,0.3*inch),P('<b>Execution guidance:</b> Record actual observations rather than restating the expected result. Attach screenshots, downloaded workbook names, API responses, or defect IDs where a case fails or needs follow-up. A PASS requires the expected result to be met with no unresolved business-blocking defect.', 'Bodyx')]

doc=SimpleDocTemplate(str(OUT),pagesize=letter,rightMargin=0.55*inch,leftMargin=0.55*inch,topMargin=0.55*inch,bottomMargin=0.62*inch,title='Payroll Panel UAT Test Plan',author='QA Team')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(f'Created {OUT} ({OUT.stat().st_size} bytes, {len(PdfReader(str(OUT)).pages)} pages)')
