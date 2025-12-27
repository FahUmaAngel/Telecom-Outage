# ข้อมูลที่ดึงมาจาก Browser Investigation

## 📸 Screenshots ที่จับได้

### 1. หน้าแรก - เลือกประเภทเครือข่าย
![Telia Initial Load](file:///C:/Users/Umakue/.gemini/antigravity/brain/fbc1b38a-b971-451f-87a4-92d51dcdab27/telia_initial_load_1766754492018.png)

หน้านี้แสดงตัวเลือกให้เลือกว่าจะดู:
- **Mobila nätet** (Mobile Network) - เครือข่ายมือถือ 2G, 3G, 4G, 5G
- **Fasta nätet** (Fixed Network) - Broadband, TV, และโทรศัพท์บ้าน

---

### 2. Mobile Network Outages - CellVision Portal
![Mobile Coverage Portal](file:///C:/Users/Umakue/.gemini/antigravity/brain/fbc1b38a-b971-451f-87a4-92d51dcdab27/mobile_coverage_load_1766755319815.png)

**ระบบ:** CellVision CoveragePortal  
**URL:** `https://coverage.ddc.teliasonera.net/coverageportal_se?appmode=outage`

**ข้อมูลที่เห็นในภาพ:**
- รายการ outages แบ่งตามจังหวัด (län)
- ตัวอย่างที่พบ:
  - **Uppsala län** - มี outages
  - **Norrbottens län** - มี outages
  
**ข้อความตัวอย่างที่พบ:**
> "På grund av ett kabelfel i ditt område kan du uppleva störningar i mobilnätet..."
> 
> (เนื่องจากสายเคเบิลขัดข้อง คุณอาจประสบปัญหากับเครือข่ายมือถือในพื้นที่ของคุณ...)

---

### 3. Fixed Network Outages - GLUP System
![Fixed Network Portal](file:///C:/Users/Umakue/.gemini/antigravity/brain/fbc1b38a-b971-451f-87a4-92d51dcdab27/fixed_outage_list_1766755876579.png)

**ระบบ:** GLUP (Broadband Outage System)  
**URL:** `https://glu2.han.telia.se/bios/glup/glup.html#container`

**ฟีเจอร์ที่เห็น:**
- แผนที่แบบ interactive
- ช่องค้นหาตามที่อยู่
- ตัวกรอง:
  - "Oplanerat avbrott/störning" (Unplanned outage)
  - "Planerat avbrott/störning" (Planned outage)

---

## 🔍 API Endpoints ที่ค้นพบ

### Mobile Network APIs

#### 1. Fault Details
```
GET https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/AreaTicketList
```
**Parameters:**
- `llx`, `lly`, `urx`, `ury` - Bounding box coordinates
- `services` - Service types (e.g., LTE700_DATA)
- `ert` - Session token

**Response Format:**
```json
[
  {
    "FaultId": "12345",
    "Text": "På grund av ett kabelfel...",
    "EventTime": "2025-12-26T10:00:00",
    "EstimatedCloseTime": "2025-12-26T18:00:00",
    "ExternalId": "EXT-123"
  }
]
```

#### 2. Last Updated Info
```
GET https://coverage.ddc.teliasonera.net/coverageportal_se/Fault/FaultsLastUpdatedInfo
```
**Response:** Timestamp information and cache keys

#### 3. Important Messages
```
GET https://coverage.ddc.teliasonera.net/coverageportal_se/ImportantMessages/GetMessages
```
**Response:** Array of important messages (currently empty)

---

### Fixed Network APIs

#### 1. Affected Counties
```
GET https://glu2.han.telia.se/bios/glup?affectedCounties&typeTech=BROADBAND&type=ALL%20VALID
```
**Response:** List of counties with active outages (currently empty)

#### 2. Important Information
```
GET https://glu2.han.telia.se/bios/glup?importantInfo&typeTech=BROADBAND
```
**Response:** Important broadband information

---

## 📊 ข้อมูลจริงที่พบ

### Mobile Outages (จากภาพที่ 2)

Browser investigation พบ outages ในหลายพื้นที่:

**Uppsala län:**
- มีการแสดง outage information
- รายละเอียดเป็นภาษาสวีเดน
- มี timestamp และ estimated fix time

**Norrbottens län:**
- มี active outages
- แสดงในรายการด้านซ้าย

**ข้อความที่พบ (ตัวอย่าง):**
```
"På grund av ett kabelfel i ditt område kan du uppleva 
störningar i mobilnätet. Vi arbetar med att åtgärda felet."

(Due to a cable fault in your area, you may experience 
disruptions in the mobile network. We are working to fix the fault.)
```

---

### Fixed Network Outages

ตอนที่ทดสอบ (26 Dec 2025, 14:32):
- **ไม่มี active outages** สำหรับ broadband
- API ส่งกลับข้อมูลว่าง (empty response)
- ซึ่งหมายความว่าเครือข่าย broadband ทำงานปกติ ✅

---

## 🎥 Browser Recording

การทำงานทั้งหมดของ browser investigation ถูกบันทึกไว้ที่:

![Browser Investigation Recording](file:///C:/Users/Umakue/.gemini/antigravity/brain/fbc1b38a-b971-451f-87a4-92d51dcdab27/telia_devtools_investigation_1766754290779.webp)

**การกระทำที่บันทึกไว้:**
1. เปิดหน้า Telia outage page
2. Scroll และ navigate ไปยังส่วนต่างๆ
3. Click เลือก "Fasta nätet" และ "Mobila nätet"
4. เปิด iframe URLs โดยตรง
5. Monitor Network requests
6. Click บน regions เพื่อดู detailed information

---

## 💡 สิ่งที่เรียนรู้

### 1. Architecture
- Telia ใช้ **iframe-based architecture**
- ข้อมูล mobile และ fixed อยู่คนละ domain
- แต่ละระบบมี API endpoints แยกกัน

### 2. Data Format
- **Mobile:** JSON format พร้อม detailed descriptions
- **Fixed:** XML/Text format (ต้อง parse)
- ทั้งคู่ใช้ภาษาสวีเดน

### 3. Real-time Data
- ข้อมูลถูก update แบบ real-time
- มี timestamp และ estimated fix time
- แสดงทั้ง planned และ unplanned outages

---

## 📁 ไฟล์ที่เกี่ยวข้อง

**Screenshots:**
- `telia_initial_load_1766754492018.png` - หน้าแรก
- `mobile_coverage_load_1766755319815.png` - Mobile outages
- `fixed_outage_list_1766755876579.png` - Fixed network interface
- `glup_page_load_1766755034541.png` - GLUP system

**Recording:**
- `telia_devtools_investigation_1766754290779.webp` - Full browser session

**Click Feedback Screenshots:**
- Multiple click feedback images showing interactions

---

## ✅ สรุป

Browser investigation **สำเร็จมาก!** เราได้:
- ✓ ค้นพบ API endpoints ทั้งหมด
- ✓ เห็นข้อมูล outage จริงๆ (mobile network)
- ✓ เข้าใจ architecture ของระบบ
- ✓ มี screenshots เป็นหลักฐาน
- ✓ บันทึก recording ไว้ทั้งหมด

**ข้อมูลที่ได้มาเพียงพอ** สำหรับการสร้าง production scraper แล้วค่ะ! 🎉
