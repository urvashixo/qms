import { configureStore, createSlice } from '@reduxjs/toolkit'

const emptyForm = { complaint_source:'', customer_name:'', product_name:'', product_strength:'', batch_number:'', affected_quantity:'', manufacturing_date:'', expiry_date:'', originating_site:'', impacted_materials:'', complaint_category:'', complaint_description:'', reporter_contact:'' }
const emptyRisk = { severity:'Pending', priority:'Pending', suggested_next_action:'Awaiting complaint details', initial_risk_assessment:'AIVOA will assess product quality risk after extracting complaint details.', root_cause_hypothesis:'', capa_recommendation:'', duplicate_hint:'No comparable complaints in the current session.' }

const complaintSlice = createSlice({
  name: 'complaint',
  initialState: { form: emptyForm, risk: emptyRisk, messages: [{ role:'assistant', type:'welcome', text:'Ready to process new complaints. Paste a customer email, describe a complaint, or upload a PDF. I will extract the record and run an initial risk assessment.' }], loading:false, committed:null, error:'' },
  reducers: {
    begin(state, action) { state.loading = true; state.error=''; state.messages.push({role:'user', text:action.payload}) },
    applyCopilot(state, action) { state.loading=false; state.form=action.payload.form; state.risk=action.payload.risk; state.messages.push({role:'assistant', type:'success', text:action.payload.message}) },
    fail(state, action) { state.loading=false; state.error=action.payload; state.messages.push({role:'assistant', type:'error', text:action.payload}) },
    setCommitted(state, action) { state.committed=action.payload },
    clearCommitted(state) { state.committed=null }
  }
})
export const { begin, applyCopilot, fail, setCommitted, clearCommitted } = complaintSlice.actions
export const store = configureStore({ reducer: { complaint: complaintSlice.reducer } })

