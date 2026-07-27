import { useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Beaker, Bot, Check, CheckCircle2, ChevronRight, CircleAlert, ClipboardCheck, FileText, LoaderCircle, Paperclip, Send, ShieldCheck, Sparkles, Upload } from 'lucide-react'
import { applyCopilot, begin, fail, setCommitted } from './store'
import { commitComplaint, sendMessage, uploadDocument } from './api'

const sectionFields = [
  { number:'01', title:'Origin & customer details', fields:[['Complaint source','complaint_source'],['Customer name','customer_name'],['Reporter contact','reporter_contact']] },
  { number:'02', title:'Product & batch identification', fields:[['Product name','product_name'],['Product strength / grade','product_strength'],['Batch / lot number','batch_number'],['Affected quantity','affected_quantity'],['Manufacturing date','manufacturing_date'],['Expiry date','expiry_date']] },
  { number:'03', title:'Facility & material impact', fields:[['Originating site block','originating_site'],['Impacted non-product materials','impacted_materials']] },
]

function Field({label, value, wide=false, multiline=false}) {
  return <label className={wide ? 'field wide' : 'field'}><span>{label}</span>{multiline ? <div className="readbox multi">{value || 'Awaiting AI extraction...'}</div> : <div className="readbox">{value || 'Awaiting AI extraction...'}</div>}</label>
}

function FormPanel() {
  const { form, risk, committed } = useSelector(s => s.complaint)
  const dispatch = useDispatch()
  const hasRecord = Boolean(form.product_name || form.customer_name || form.complaint_description)
  const [saving, setSaving] = useState(false)
  const commit = async () => {
    if (!hasRecord) return
    setSaving(true)
    try { dispatch(setCommitted(await commitComplaint({form, risk}))) } catch (e) { alert(e.message) } finally { setSaving(false) }
  }
  return <main className="form-panel">
    <header className="page-header">
      <div className="eyebrow"><Sparkles size={15}/> AI-powered quality intake</div>
      <div className="title-row"><div><h1>Log Customer Complaint</h1><p>API &amp; FDF Quality Assurance Module</p></div><div className={hasRecord ? 'status status-ready' : 'status'}><span></span>{hasRecord ? 'AI assessed' : 'Pending triage'}</div></div>
    </header>
    <div className="form-scroll">
      {sectionFields.map(section => <section className="form-section" key={section.number}><div className="section-heading"><b>{section.number}</b> {section.title}</div><div className="field-grid">{section.fields.map(([label,key]) => <Field key={key} label={label} value={form[key]} />)}</div></section>)}
      <section className="form-section"><div className="section-heading"><b>04</b> Defect analysis</div><div className="field-grid"><Field label="Complaint category" value={form.complaint_category} wide/><Field label="Complaint description" value={form.complaint_description} wide multiline/></div></section>
      <section className="risk-card"><div className="risk-heading"><ShieldCheck size={21}/> <span>AI copilot risk assessment</span><small>dynamic analysis</small></div><div className="risk-grid"><Field label="Severity (suggested)" value={risk.severity}/><Field label="Priority" value={risk.priority}/><Field label="Suggested next action" value={risk.suggested_next_action} wide/><Field label="Initial risk assessment" value={risk.initial_risk_assessment} wide multiline/><Field label="Root cause hypothesis" value={risk.root_cause_hypothesis} wide multiline/><Field label="CAPA recommendation" value={risk.capa_recommendation} wide multiline/></div><div className="duplicate"><CircleAlert size={15}/>{risk.duplicate_hint}</div></section>
      <button className="commit" disabled={!hasRecord || saving} onClick={commit}>{saving ? <LoaderCircle className="spin" size={19}/> : <ClipboardCheck size={19}/>} {committed ? `${committed.reference} committed` : 'Commit to QMS ledger'}<ChevronRight size={18}/></button>
      <p className="audit-note">{committed ? 'Immutable ledger record created. ' : ''}All fields are controlled by AIVOA Copilot to maintain an attributable intake trail.</p>
    </div>
  </main>
}

function Message({message}) {
  if (message.role === 'user') return <div className="message user-message"><div>{message.text}</div><span className="user-dot">You</span></div>
  return <div className={`message assistant-message ${message.type || ''}`}><div className="message-icon">{message.type === 'success' ? <Check size={18}/> : message.type === 'error' ? <CircleAlert size={18}/> : <Sparkles size={18}/>}</div><p>{message.text}</p></div>
}

function CopilotPanel() {
  const { form, risk, messages, loading, error } = useSelector(s => s.complaint)
  const dispatch = useDispatch(); const [text, setText] = useState(''); const fileRef = useRef()
  const process = async (value) => {
    const message = value.trim(); if (!message || loading) return
    dispatch(begin(message)); setText('')
    try { dispatch(applyCopilot(await sendMessage({message, current_form:form, current_risk:risk}))) } catch (e) { dispatch(fail(e.message)) }
  }
  const upload = async (file) => {
    if (!file || loading) return
    dispatch(begin(`Uploaded ${file.name} for document extraction.`))
    try { dispatch(applyCopilot(await uploadDocument(file))) } catch (e) { dispatch(fail(e.message)) }
    if (fileRef.current) fileRef.current.value = ''
  }
  return <aside className="copilot-panel">
    <header className="copilot-header"><div className="copilot-title"><div className="bot-badge"><Beaker size={22}/></div><div><h2>AIVOA Copilot</h2><p>Complaint intelligence workspace</p></div></div><div className="online"><span></span>Online</div></header>
    <div className="messages">{messages.map((message,index) => <Message key={index} message={message}/>)}{loading && <div className="thinking"><LoaderCircle className="spin" size={17}/> AIVOA is extracting and assessing...</div>}{error && <small className="connection-note">Check that the FastAPI service is running on port 8000.</small>}</div>
    <div className="composer-wrap"><div className="drop-zone" onClick={() => fileRef.current?.click()}><Upload size={16}/><span>Upload PDF, email, or text</span><input ref={fileRef} type="file" accept=".pdf,.txt,.eml" onChange={e => upload(e.target.files?.[0])}/></div><div className="composer"><button className="attach" onClick={() => fileRef.current?.click()} aria-label="Attach complaint file"><Paperclip size={21}/></button><textarea rows="2" placeholder="Describe a complaint or correct a field..." value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); process(text) }}}/><button className="send" disabled={!text.trim() || loading} onClick={() => process(text)} aria-label="Send message"><Send size={18}/></button></div><div className="powered"><Bot size={13}/> Powered by LangGraph • Groq</div></div>
  </aside>
}

export default function App() { return <div className="app-shell"><FormPanel/><CopilotPanel/></div> }

