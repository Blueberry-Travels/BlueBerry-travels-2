import React from 'react';
import Head from 'next/head';

export default function Flowchart() {
    return (
        <>
            <Head>
                <title>Blueberry Travels - Flowchart</title>
            </Head>
            {/* Original Body Migrated to JSX */}
            

<h1>Blueberry Travel Solutions — Frontend Logic Flowchart</h1>
<p className="subtitle">For developers. Each tab is a separate flow. Open in any browser — no software required.</p>

<div className="tabs">
    <div className="tab active" >User Journey</div>
    <div className="tab" >DIY Builder</div>
    <div className="tab" >Booking Flow</div>
    <div className="tab" >Page Map</div>
    <div className="tab" >Partner Portal</div>
    <div className="tab" >API Hooks</div>
</div>

{/*  ══════════════════════════════════════════════
     TAB 1 — USER JOURNEY
════════════════════════════════════════════════  */}
<div className="diagram active" id="tab-user-journey">
<svg viewBox="0 0 900 820" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#555" strokeWidth="1.5"/>
  </marker>
  <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#376121" strokeWidth="1.5"/>
  </marker>
  <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#b85c2a" strokeWidth="1.5"/>
  </marker>
</defs>

{/*  LANDING  */}
<rect className="box-dark" x="340" y="20" width="220" height="44" rx="10"/>
<text className="lbl-white" x="450" y="47" text-anchor="middle">Landing Page (index.html)</text>

{/*  BROWSE without login  */}
<text className="note" x="450" y="82" text-anchor="middle">No login required to browse, quiz, build itinerary</text>

{/*  Main nav options  */}
<line className="arr" x1="360" y1="64" x2="160" y2="120"/>
<line className="arr" x1="420" y1="64" x2="340" y2="120"/>
<line className="arr" x1="450" y1="64" x2="450" y2="120"/>
<line className="arr" x1="480" y1="64" x2="560" y2="120"/>
<line className="arr" x1="520" y1="64" x2="720" y2="120"/>

<rect className="box-green" x="80"  y="120" width="140" height="36" rx="8"/>
<text className="lbl-green" x="150" y="143" text-anchor="middle">DIY Builder</text>
<rect className="box-green" x="250" y="120" width="140" height="36" rx="8"/>
<text className="lbl-green" x="320" y="143" text-anchor="middle">Packages</text>
<rect className="box-green" x="380" y="120" width="140" height="36" rx="8"/>
<text className="lbl-green" x="450" y="143" text-anchor="middle">Events</text>
<rect className="box-green" x="510" y="120" width="140" height="36" rx="8"/>
<text className="lbl-green" x="580" y="143" text-anchor="middle">Hobbyist</text>
<rect className="box-green" x="650" y="120" width="160" height="36" rx="8"/>
<text className="lbl-green" x="730" y="143" text-anchor="middle">Workations / Retreats</text>

{/*  Converge to itinerary build  */}
<line className="arr" x1="150" y1="156" x2="380" y2="220"/>
<line className="arr" x1="320" y1="156" x2="410" y2="220"/>
<line className="arr" x1="450" y1="156" x2="450" y2="220"/>
<line className="arr" x1="580" y1="156" x2="490" y2="220"/>
<line className="arr" x1="730" y1="156" x2="520" y2="220"/>

<rect className="box" x="320" y="220" width="260" height="44" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="247" text-anchor="middle">User builds / selects itinerary</text>

{/*  Gate  */}
<line className="arr" x1="450" y1="264" x2="450" y2="300"/>
<rect className="box-amber" x="330" y="300" width="240" height="44" rx="8"/>
<text className="lbl-amber" x="450" y="327" text-anchor="middle">&#9650; GATE: Click "Create"</text>

{/*  Two paths: logged in vs not  */}
<line className="arr" x1="330" y1="322" x2="200" y2="370"/>
<line className="arr" x1="570" y1="322" x2="680" y2="370"/>

<rect className="box" x="100" y="370" width="200" height="44" rx="8" stroke="#4a6274"/>
<text className="lbl-slate" x="200" y="387" text-anchor="middle">Not logged in</text>
<text className="sub"       x="200" y="402" text-anchor="middle">Watermarked preview shown</text>
<rect className="box-green" x="580" y="370" width="200" height="44" rx="8"/>
<text className="lbl-green" x="680" y="387" text-anchor="middle">Logged in</text>
<text className="sub"       x="680" y="402" text-anchor="middle">Full itinerary created</text>

{/*  Not logged in → login  */}
<line className="arr" x1="200" y1="414" x2="200" y2="460"/>
<rect className="box-amber" x="100" y="460" width="200" height="36" rx="8"/>
<text className="lbl-amber" x="200" y="483" text-anchor="middle">Login / Register + KYC</text>

{/*  Both converge to dashboard  */}
<line className="arr" x1="200" y1="496" x2="380" y2="560"/>
<line className="arr" x1="680" y1="414" x2="520" y2="560"/>

<rect className="box-dark" x="300" y="560" width="300" height="44" rx="10"/>
<text className="lbl-white" x="450" y="587" text-anchor="middle">Dashboard — Pre-Booking</text>

{/*  Dashboard actions  */}
<line className="arr" x1="380" y1="604" x2="240" y2="650"/>
<line className="arr" x1="450" y1="604" x2="450" y2="650"/>
<line className="arr" x1="520" y1="604" x2="660" y2="650"/>

<rect className="box-green" x="140" y="650" width="180" height="36" rx="8"/>
<text className="lbl-green" x="230" y="673" text-anchor="middle">Select Assistance Tier</text>
<rect className="box-green" x="360" y="650" width="180" height="36" rx="8"/>
<text className="lbl-green" x="450" y="673" text-anchor="middle">Review Itinerary</text>
<rect className="box-green" x="560" y="650" width="180" height="36" rx="8"/>
<text className="lbl-green" x="650" y="673" text-anchor="middle">Sign NOC / Waiver</text>

{/*  All lead to payment  */}
<line className="arr" x1="230" y1="686" x2="380" y2="740"/>
<line className="arr" x1="450" y1="686" x2="450" y2="740"/>
<line className="arr" x1="650" y1="686" x2="520" y2="740"/>

<rect className="box-amber" x="310" y="740" width="280" height="44" rx="10"/>
<text className="lbl-amber" x="450" y="767" text-anchor="middle">Confirm &amp; Pay (Razorpay)</text>

{/*  Final state  */}
<line className="arr-green" x1="450" y1="784" x2="450" y2="800"/>
<text className="lbl-green" x="450" y="816" text-anchor="middle">&#10003; Booking Confirmed — Partners Notified</text>

{/*  Legend  */}
<rect fill="#ebf6e7" stroke="#376121" strokeWidth="1" x="20" y="760" width="12" height="12" rx="2"/>
<text className="note" x="36" y="771">Customer action</text>
<rect fill="#fff8e8" stroke="#b85c2a" strokeWidth="1" x="20" y="778" width="12" height="12" rx="2"/>
<text className="note" x="36" y="789">Gate / decision</text>
<rect fill="#376121" x="20" y="796" width="12" height="12" rx="2"/>
<text className="note" x="36" y="807">System / page</text>
</svg>
</div>

{/*  ══════════════════════════════════════════════
     TAB 2 — DIY BUILDER FLOW
════════════════════════════════════════════════  */}
<div className="diagram" id="tab-diy-flow">
<svg viewBox="0 0 900 700" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arr2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#555" strokeWidth="1.5"/>
  </marker>
  <marker id="arr2g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#376121" strokeWidth="1.5"/>
  </marker>
</defs>

{/*  Start  */}
<rect className="box-dark" x="340" y="20" width="220" height="40" rx="10"/>
<text className="lbl-white" x="450" y="45" text-anchor="middle">diy.html — Loads</text>

{/*  Filter bar  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="450" y1="60" x2="450" y2="90"/>
<rect className="box" x="300" y="90" width="300" height="36" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="113" text-anchor="middle">Filter Bar (search + filter button)</text>
<text className="sub" x="450" y="130" text-anchor="middle">→ /api/activities/search/?q=... (Django REST)</text>

{/*  Map  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="450" y1="136" x2="450" y2="166"/>
<rect className="box-green" x="290" y="166" width="320" height="40" rx="8"/>
<text className="lbl-green" x="450" y="191" text-anchor="middle">India Map SVG — 5 Clickable Regions</text>

{/*  5 regions  */}
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr2g)" x1="360" y1="206" x2="120" y2="250"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr2g)" x1="400" y1="206" x2="260" y2="250"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr2g)" x1="450" y1="206" x2="450" y2="250"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr2g)" x1="500" y1="206" x2="640" y2="250"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr2g)" x1="540" y1="206" x2="780" y2="250"/>

<rect className="box-green" x="50"  y="250" width="140" height="32" rx="6"/>
<text className="lbl-green" x="120" y="271" text-anchor="middle">Uttar (North)</text>
<rect className="box-green" x="195" y="250" width="140" height="32" rx="6"/>
<text className="lbl-green" x="265" y="271" text-anchor="middle">Pashchim (West)</text>
<rect className="box-green" x="370" y="250" width="160" height="32" rx="6"/>
<text className="lbl-green" x="450" y="271" text-anchor="middle">Madhyam (Central)</text>
<rect className="box-green" x="566" y="250" width="148" height="32" rx="6"/>
<text className="lbl-green" x="640" y="271" text-anchor="middle">Poorabh (East)</text>
<rect className="box-green" x="716" y="250" width="134" height="32" rx="6"/>
<text className="lbl-green" x="783" y="271" text-anchor="middle">Dakshin (South)</text>

{/*  Click region → detail panel  */}
<text className="note" x="450" y="304" text-anchor="middle">User clicks any region →</text>
<rect className="box" x="260" y="314" width="380" height="52" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="336" text-anchor="middle">Region Detail Panel appears</text>
<text className="sub" x="450" y="354" text-anchor="middle">States as pills + Activity tiles (admin picks ★ highlighted)</text>
<text className="sub" x="450" y="368" text-anchor="middle">{"Data source: /api/regions/{id}/activities/"}</text>

{/*  User adds activities  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="450" y1="366" x2="450" y2="396"/>
<rect className="box-amber" x="290" y="396" width="320" height="40" rx="8"/>
<text className="lbl-amber" x="450" y="421" text-anchor="middle">User clicks activity → Added to Itinerary Tray</text>

{/*  Tray  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="450" y1="436" x2="450" y2="466"/>
<rect className="box" x="270" y="466" width="360" height="52" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="488" text-anchor="middle">Itinerary Tray (bottom of page)</text>
<text className="sub" x="450" y="506" text-anchor="middle">Shows selected activities, day order, estimated time</text>

{/*  Two actions  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="380" y1="518" x2="260" y2="560"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr2)" x1="520" y1="518" x2="640" y2="560"/>

<rect className="box" x="160" y="560" width="200" height="36" rx="8" stroke="#888"/>
<text className="lbl" x="260" y="583" text-anchor="middle">Save Draft</text>
<text className="sub" x="260" y="610" text-anchor="middle">POST /api/itinerary/draft/</text>
<text className="sub" x="260" y="624" text-anchor="middle">Requires login gate</text>

<rect className="box-dark" x="540" y="560" width="200" height="36" rx="10"/>
<text className="lbl-white" x="640" y="583" text-anchor="middle">Create Itinerary &#8594;</text>
<text className="sub" x="640" y="610" text-anchor="middle">POST /api/itinerary/create/</text>
<text className="sub" x="640" y="624" text-anchor="middle">Triggers graph engine (backend)</text>
<text className="sub" x="640" y="638" text-anchor="middle">→ Redirects to dashboard.html</text>

{/*  Note about watermark  */}
<rect fill="#fff8e8" stroke="#b85c2a" strokeWidth="1" x="20" y="560" width="130" height="50" rx="8"/>
<text className="note" x="85" y="578" text-anchor="middle">If not logged in:</text>
<text className="note" x="85" y="593" text-anchor="middle">Show watermarked</text>
<text className="note" x="85" y="608" text-anchor="middle">preview only</text>
</svg>
</div>

{/*  ══════════════════════════════════════════════
     TAB 3 — BOOKING FLOW
════════════════════════════════════════════════  */}
<div className="diagram" id="tab-booking-flow">
<svg viewBox="0 0 900 760" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arr3" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#555" strokeWidth="1.5"/>
  </marker>
</defs>

{/*  Step boxes  */}
<rect className="box-dark" x="310" y="20" width="280" height="40" rx="10"/>
<text className="lbl-white" x="450" y="45" text-anchor="middle">dashboard.html loads with itinerary</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="60" x2="450" y2="90"/>

{/*  Step 1  */}
<rect className="box-green" x="290" y="90" width="320" height="50" rx="8"/>
<text className="lbl-green" x="450" y="111" text-anchor="middle">Step 1: Review Itinerary</text>
<text className="sub" x="450" y="128" text-anchor="middle">View day-by-day plan. Edit if needed → re-call /api/itinerary/{"{id}"}/</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="140" x2="450" y2="170"/>

{/*  Step 2  */}
<rect className="box-green" x="290" y="170" width="320" height="50" rx="8"/>
<text className="lbl-green" x="450" y="191" text-anchor="middle">Step 2: Select Assistance Tier</text>
<text className="sub" x="450" y="208" text-anchor="middle">Self / Guided / Concierge / Premium → updates bill</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="220" x2="450" y2="250"/>

{/*  Step 3  */}
<rect className="box-green" x="290" y="250" width="320" height="50" rx="8"/>
<text className="lbl-green" x="450" y="271" text-anchor="middle">Step 3: Add Attendees</text>
<text className="sub" x="450" y="288" text-anchor="middle">Name, contact, KYC tier per person. POST /api/attendees/</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="300" x2="450" y2="330"/>

{/*  Step 4 KYC  */}
<rect className="box-amber" x="270" y="330" width="360" height="60" rx="8"/>
<text className="lbl-amber" x="450" y="353" text-anchor="middle">Step 4: KYC Verification (per attendee)</text>
<text className="sub" x="450" y="370" text-anchor="middle">High-risk: Aadhaar + face match + OTP (UIDAI API)</text>
<text className="sub" x="450" y="384" text-anchor="middle">Casual: Mobile OTP + name only</text>

{/*  Branch: KYC pass / fail  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="360" y1="390" x2="220" y2="430"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="540" y1="390" x2="680" y2="430"/>

<rect className="box-red" x="120" y="430" width="200" height="36" rx="8"/>
<text x="220" y="453" text-anchor="middle" font-size="12" font-weight="700" fill="#c0530a" font-family="Arial">KYC Failed</text>
<text className="sub" x="220" y="480" text-anchor="middle">7-day escalation ladder</text>
<text className="sub" x="220" y="494" text-anchor="middle">Replacement attendee option</text>

<rect className="box-green" x="580" y="430" width="200" height="36" rx="8"/>
<text className="lbl-green" x="680" y="453" text-anchor="middle">KYC Passed &#10003;</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="680" y1="466" x2="680" y2="510"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="550" y1="510" x2="450" y2="556"/>

{/*  Step 5 NOC  */}
<rect className="box-green" x="500" y="510" width="280" height="40" rx="8"/>
<text className="lbl-green" x="640" y="535" text-anchor="middle">Step 5: Sign NOC / Waiver (digital)</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="556" x2="450" y2="586"/>

{/*  Step 6 Bill  */}
<rect className="box" x="290" y="586" width="320" height="50" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="607" text-anchor="middle">Step 6: Review Final Bill</text>
<text className="sub" x="450" y="624" text-anchor="middle">Base + Activities + Tier + Emergency Cover + GST</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="636" x2="450" y2="666"/>

{/*  Step 7 Payment  */}
<rect className="box-amber" x="300" y="666" width="300" height="40" rx="8"/>
<text className="lbl-amber" x="450" y="691" text-anchor="middle">Step 7: Pay (Razorpay Gateway)</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr3)" x1="450" y1="706" x2="450" y2="730"/>
<rect className="box-dark" x="300" y="730" width="300" height="24" rx="8"/>
<text className="lbl-white" x="450" y="747" text-anchor="middle">&#10003; Booking Confirmed — Frame State: Booked</text>
</svg>
</div>

{/*  ══════════════════════════════════════════════
     TAB 4 — PAGE MAP
════════════════════════════════════════════════  */}
<div className="diagram" id="tab-page-map">
<svg viewBox="0 0 900 540" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arr4" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#999" strokeWidth="1.2"/>
  </marker>
</defs>

{/*  Root  */}
<rect className="box-dark" x="360" y="20" width="180" height="36" rx="10"/>
<text className="lbl-white" x="450" y="43" text-anchor="middle">index.html (Home)</text>

{/*  Shared shell elements  */}
<rect fill="none" stroke="#ccc" strokeDasharray="4 3" x="20" y="70" width="860" height="44" rx="8"/>
<text className="sub" x="450" y="88" text-anchor="middle">SHARED ON ALL PAGES: Topbar + Navbar spacer + Sticky Navbar + AI Bubble + Sidebar + Footer</text>
<text className="sub" x="450" y="103" text-anchor="middle">Topbar hides on scroll-down · Navbar pins at top · AI bubble bottom-right fixed</text>

{/*  Level 2 pages  */}
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="370" y1="56" x2="80" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="400" y1="56" x2="220" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="420" y1="56" x2="340" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="450" y1="56" x2="450" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="480" y1="56" x2="560" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="500" y1="56" x2="680" y2="140"/>
<line stroke="#999" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="520" y1="56" x2="800" y2="140"/>

<rect className="box-green" x="30"  y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="80"  y="160" text-anchor="middle">diy.html</text>
<rect className="box-green" x="160" y="140" width="120" height="30" rx="6"/>
<text className="lbl-green" x="220" y="160" text-anchor="middle">packages.html</text>
<rect className="box-green" x="290" y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="340" y="160" text-anchor="middle">events.html</text>
<rect className="box-green" x="400" y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="450" y="160" text-anchor="middle">hobbyist.html</text>
<rect className="box-green" x="510" y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="560" y="160" text-anchor="middle">workations</text>
<rect className="box-green" x="630" y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="680" y="160" text-anchor="middle">retreats.html</text>
<rect className="box-green" x="750" y="140" width="100" height="30" rx="6"/>
<text className="lbl-green" x="800" y="160" text-anchor="middle">misc.html</text>

{/*  All lead to quiz or dashboard  */}
<text className="note" x="450" y="210" text-anchor="middle">All pages link to quiz.html (travel style matcher) and dashboard.html (booking)</text>

<rect className="box-slate" x="200" y="222" width="140" height="30" rx="6"/>
<text className="lbl-slate" x="270" y="242" text-anchor="middle">quiz.html</text>
<rect className="box-dark"  x="370" y="222" width="160" height="30" rx="10"/>
<text className="lbl-white" x="450" y="242" text-anchor="middle">dashboard.html</text>
<rect className="box-slate" x="550" y="222" width="140" height="30" rx="6"/>
<text className="lbl-slate" x="620" y="242" text-anchor="middle">blog.html</text>

{/*  Dashboard children  */}
<text className="note" x="450" y="286" text-anchor="middle">dashboard.html sub-flows:</text>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="400" y1="252" x2="240" y2="300"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="450" y1="252" x2="450" y2="300"/>
<line stroke="#376121" strokeWidth="1.2" fill="none" marker-end="url(#arr4)" x1="500" y1="252" x2="660" y2="300"/>

<rect className="box-green" x="140" y="300" width="180" height="36" rx="6"/>
<text className="lbl-green" x="230" y="318" text-anchor="middle">Tier Selection</text>
<text className="sub" x="230" y="332" text-anchor="middle">4 assistance tiers</text>
<rect className="box-green" x="360" y="300" width="180" height="36" rx="6"/>
<text className="lbl-green" x="450" y="318" text-anchor="middle">Itinerary Review</text>
<text className="sub" x="450" y="332" text-anchor="middle">Edit / confirm</text>
<rect className="box-green" x="580" y="300" width="180" height="36" rx="6"/>
<text className="lbl-green" x="670" y="318" text-anchor="middle">Bill + Payment</text>
<text className="sub" x="670" y="332" text-anchor="middle">Razorpay integration</text>

{/*  Standalone pages  */}
<text className="note" x="450" y="380" text-anchor="middle">Standalone / utility pages (linked from footer and sidebar):</text>
<rect className="box" x="60"  y="395" width="100" height="28" rx="6" stroke="#ccc"/>
<text className="sub" x="110" y="414" text-anchor="middle">legal.html</text>
<rect className="box" x="175" y="395" width="100" height="28" rx="6" stroke="#ccc"/>
<text className="sub" x="225" y="414" text-anchor="middle">privacy.html</text>
<rect className="box" x="360" y="395" width="180" height="28" rx="6" stroke="#b85c2a"/>
<text x="450" y="414" text-anchor="middle" font-size="12" fill="#b85c2a" font-weight="700" font-family="Arial">partner_portal.html</text>
<text className="sub" x="450" y="432" text-anchor="middle">Separate file — shared hosting</text>

{/*  Note box  */}
<rect fill="#fff8e8" stroke="#b85c2a" strokeWidth="1" x="560" y="390" width="300" height="60" rx="8"/>
<text className="note" x="710" y="408" text-anchor="middle">Partner Portal is a standalone file.</text>
<text className="note" x="710" y="424" text-anchor="middle">No shared CSS dependency with</text>
<text className="note" x="710" y="440" text-anchor="middle">customer site. Deploy separately.</text>
</svg>
</div>

{/*  ══════════════════════════════════════════════
     TAB 5 — PARTNER PORTAL FLOW
════════════════════════════════════════════════  */}
<div className="diagram" id="tab-partner-flow">
<svg viewBox="0 0 900 620" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arr5" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#555" strokeWidth="1.5"/>
  </marker>
</defs>

<rect className="box-dark" x="300" y="20" width="300" height="40" rx="10"/>
<text className="lbl-white" x="450" y="45" text-anchor="middle">partner_portal.html — Loads</text>

{/*  Auth check  */}
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="450" y1="60" x2="450" y2="90"/>
<rect className="box-amber" x="300" y="90" width="300" height="40" rx="8"/>
<text className="lbl-amber" x="450" y="115" text-anchor="middle">&#9650; Auth Check: Partner session valid?</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="350" y1="110" x2="160" y2="150"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="550" y1="110" x2="680" y2="150"/>

<rect className="box-red" x="80"  y="150" width="160" height="32" rx="8"/>
<text x="160" y="171" text-anchor="middle" font-size="12" fill="#c0530a" font-weight="700" font-family="Arial">Not auth → Login page</text>

<rect className="box-green" x="600" y="150" width="160" height="32" rx="8"/>
<text className="lbl-green" x="680" y="171" text-anchor="middle">Auth &#10003; → Dashboard</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="680" y1="182" x2="680" y2="210"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="620" y1="210" x2="450" y2="250"/>

{/*  Sidebar sections  */}
<rect className="box" x="250" y="250" width="400" height="36" rx="8" stroke="#888"/>
<text className="lbl" x="450" y="273" text-anchor="middle">Sidebar Navigation — 8 Sections</text>

<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="310" y1="286" x2="100" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="350" y1="286" x2="230" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="390" y1="286" x2="350" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="430" y1="286" x2="460" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="480" y1="286" x2="570" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="520" y1="286" x2="680" y2="330"/>
<line stroke="#555" strokeWidth="1.5" fill="none" marker-end="url(#arr5)" x1="560" y1="286" x2="790" y2="330"/>

<rect className="box-green" x="30"  y="330" width="140" height="30" rx="6"/>
<text className="lbl-green" x="100" y="350" text-anchor="middle">Dashboard</text>
<rect className="box-green" x="175" y="330" width="110" height="30" rx="6"/>
<text className="lbl-green" x="230" y="350" text-anchor="middle">Bookings</text>
<rect className="box-green" x="295" y="330" width="110" height="30" rx="6"/>
<text className="lbl-green" x="350" y="350" text-anchor="middle">Availability</text>
<rect className="box-green" x="415" y="330" width="100" height="30" rx="6"/>
<text className="lbl-green" x="465" y="350" text-anchor="middle">Earnings</text>
<rect className="box-green" x="525" y="330" width="100" height="30" rx="6"/>
<text className="lbl-green" x="575" y="350" text-anchor="middle">Inventory</text>
<rect className="box-green" x="635" y="330" width="110" height="30" rx="6"/>
<text className="lbl-green" x="690" y="350" text-anchor="middle">Templates</text>
<rect className="box-green" x="755" y="330" width="110" height="30" rx="6"/>
<text className="lbl-green" x="810" y="350" text-anchor="middle">KYC/Settings</text>

{/*  Key actions per section  */}
<text className="note" x="450" y="396" text-anchor="middle">Key actions per section (all call Django REST APIs):</text>

<rect className="box" x="20" y="410" width="188" height="80" rx="6" stroke="#ccc"/>
<text className="sub" x="114" y="428" text-anchor="middle" font-weight="700">Bookings</text>
<text className="sub" x="114" y="444" text-anchor="middle">Accept / Reject request</text>
<text className="sub" x="114" y="458" text-anchor="middle">→ PATCH /api/bookings/{"{id}"}/</text>
<text className="sub" x="114" y="472" text-anchor="middle">Self-report failure</text>
<text className="sub" x="114" y="486" text-anchor="middle">→ POST /api/partner/failure/</text>

<rect className="box" x="218" y="410" width="188" height="80" rx="6" stroke="#ccc"/>
<text className="sub" x="312" y="428" text-anchor="middle" font-weight="700">Availability Calendar</text>
<text className="sub" x="312" y="444" text-anchor="middle">Set available dates</text>
<text className="sub" x="312" y="458" text-anchor="middle">→ POST /api/partner/availability/</text>
<text className="sub" x="312" y="472" text-anchor="middle">Block dates</text>
<text className="sub" x="312" y="486" text-anchor="middle">→ POST /api/partner/block/</text>

<rect className="box" x="416" y="410" width="188" height="80" rx="6" stroke="#ccc"/>
<text className="sub" x="510" y="428" text-anchor="middle" font-weight="700">Earnings</text>
<text className="sub" x="510" y="444" text-anchor="middle">View payout history</text>
<text className="sub" x="510" y="458" text-anchor="middle">→ GET /api/partner/payouts/</text>
<text className="sub" x="510" y="472" text-anchor="middle">Commission: 5–25%</text>
<text className="sub" x="510" y="486" text-anchor="middle">(set by admin per partner)</text>

<rect className="box" x="614" y="410" width="188" height="80" rx="6" stroke="#ccc"/>
<text className="sub" x="708" y="428" text-anchor="middle" font-weight="700">Inventory / KYC</text>
<text className="sub" x="708" y="444" text-anchor="middle">Add/edit services</text>
<text className="sub" x="708" y="458" text-anchor="middle">→ POST /api/partner/inventory/</text>
<text className="sub" x="708" y="472" text-anchor="middle">Upload KYC docs</text>
<text className="sub" x="708" y="486" text-anchor="middle">→ POST /api/partner/kyc/</text>

{/*  Note  */}
<rect fill="#ebf6e7" stroke="#376121" strokeWidth="1" x="180" y="510" width="540" height="44" rx="8"/>
<text className="note" x="450" y="528" text-anchor="middle">Partner portal is pure static HTML — all dynamic data loaded via fetch() to Django REST APIs.</text>
<text className="note" x="450" y="546" text-anchor="middle">Auth token stored in sessionStorage. Hosted separately from customer site.</text>
</svg>
</div>

{/*  ══════════════════════════════════════════════
     TAB 6 — API HOOKS MAP
════════════════════════════════════════════════  */}
<div className="diagram" id="tab-api-map">
<svg viewBox="0 0 900 680" xmlns="http://www.w3.org/2000/svg">

<text className="lbl" x="450" y="30" text-anchor="middle">Frontend → Backend API Mapping (Django REST Framework)</text>
<text className="sub" x="450" y="48" text-anchor="middle">All endpoints prefixed with /api/v1/. Auth via JWT token in Authorization header.</text>

{/*  Headers  */}
<rect fill="#1a2e10" x="20" y="60" width="260" height="30" rx="6"/>
<text className="lbl-white" x="150" y="80" text-anchor="middle">Page / Action</text>
<rect fill="#1a2e10" x="290" y="60" width="280" height="30" rx="6"/>
<text className="lbl-white" x="430" y="80" text-anchor="middle">Endpoint</text>
<rect fill="#1a2e10" x="580" y="60" width="300" height="30" rx="6"/>
<text className="lbl-white" x="730" y="80" text-anchor="middle">Method / Notes</text>

{/*  Rows  */}
<rect className="box" x="20"  y="95" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="114">index.html — Hero content</text>
<rect className="box" x="290" y="95" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="114">/api/v1/featured/</text>
<rect className="box" x="580" y="95" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="114">GET — admin-curated highlight tiles</text>

<rect className="box" x="20"  y="128" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="147">DIY — Load region activities</text>
<rect className="box" x="290" y="128" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="147">{"/api/v1/regions/{id}/activities/"}</text>
<rect className="box" x="580" y="128" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="147">GET — returns activities + admin picks</text>

<rect className="box" x="20"  y="161" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="180">DIY — Search activities</text>
<rect className="box" x="290" y="161" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="180">/api/v1/activities/search/?q=</text>
<rect className="box" x="580" y="161" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="180">GET — full-text search</text>

<rect className="box" x="20"  y="194" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="213">DIY — Create itinerary</text>
<rect className="box" x="290" y="194" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="213">/api/v1/itinerary/create/</text>
<rect className="box" x="580" y="194" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="213">POST — triggers graph engine</text>

<rect className="box" x="20"  y="227" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="246">DIY — Save draft</text>
<rect className="box" x="290" y="227" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="246">/api/v1/itinerary/draft/</text>
<rect className="box" x="580" y="227" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="246">POST — login required</text>

<rect className="box" x="20"  y="260" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="279">Dashboard — Load itinerary</text>
<rect className="box" x="290" y="260" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="279">{"/api/v1/itinerary/{id}/"}</text>
<rect className="box" x="580" y="260" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="279">GET — full frame with pricing</text>

<rect className="box" x="20"  y="293" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="312">Dashboard — Select tier</text>
<rect className="box" x="290" y="293" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="312">{"/api/v1/itinerary/{id}/tier/"}</text>
<rect className="box" x="580" y="293" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="312">PATCH — updates bill total</text>

<rect className="box" x="20"  y="326" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="345">Dashboard — KYC (customer)</text>
<rect className="box" x="290" y="326" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="345">/api/v1/kyc/verify/</text>
<rect className="box" x="580" y="326" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="345">POST — calls UIDAI API internally</text>

<rect className="box" x="20"  y="359" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="378">Dashboard — Confirm &amp; Pay</text>
<rect className="box" x="290" y="359" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="378">/api/v1/booking/confirm/</text>
<rect className="box" x="580" y="359" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="378">POST — triggers Razorpay order</text>

<rect className="box" x="20"  y="392" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="411">AI Bubble — Send message</text>
<rect className="box" x="290" y="392" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="411">/api/v1/assistant/</text>
<rect className="box" x="580" y="392" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="411">POST {"{message, session_id}"}</text>

<rect className="box" x="20"  y="425" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="444">Auth — Login / Register</text>
<rect className="box" x="290" y="425" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="444">/api/v1/auth/login/ , /register/</text>
<rect className="box" x="580" y="425" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="444">POST — returns JWT token</text>

{/*  Partner Portal rows  */}
<rect fill="#1a2e10" x="20" y="468" width="860" height="24" rx="4"/>
<text className="lbl-white" x="450" y="485" text-anchor="middle">Partner Portal Endpoints</text>

<rect className="box" x="20"  y="497" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="516">Partner — Accept/Reject booking</text>
<rect className="box" x="290" y="497" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="516">{"/api/v1/partner/bookings/{id}/"}</text>
<rect className="box" x="580" y="497" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="516">PATCH {"{status: confirmed/rejected}"}</text>

<rect className="box" x="20"  y="530" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="549">Partner — Set availability</text>
<rect className="box" x="290" y="530" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="549">/api/v1/partner/availability/</text>
<rect className="box" x="580" y="530" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="549">POST {"{dates, slots, service_id}"}</text>

<rect className="box" x="20"  y="563" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="582">Partner — Report failure</text>
<rect className="box" x="290" y="563" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="582">/api/v1/partner/failure/</text>
<rect className="box" x="580" y="563" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="582">POST — triggers recovery protocol</text>

<rect className="box" x="20"  y="596" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="615">Partner — Earnings / Payouts</text>
<rect className="box" x="290" y="596" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="615">/api/v1/partner/payouts/</text>
<rect className="box" x="580" y="596" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="615">GET — paginated payout history</text>

<rect className="box" x="20"  y="629" width="260" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="30" y="648">Partner — KYC upload</text>
<rect className="box" x="290" y="629" width="280" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="300" y="648">/api/v1/partner/kyc/</text>
<rect className="box" x="580" y="629" width="300" height="28" rx="4" stroke="#eee"/>
<text className="sub" x="590" y="648">POST multipart/form-data</text>
</svg>
</div>



        </>
    );
}
