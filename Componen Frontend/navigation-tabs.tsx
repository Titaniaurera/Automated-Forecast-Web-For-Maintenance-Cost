"use client"


import {
  useRef,
  useState
} from "react"


import {
  Download,
} from "lucide-react"





// ============================================================
// PROPS
// ============================================================


interface NavigationTabsProps {


  setForecastData:

  React.Dispatch<

    React.SetStateAction<any[]>

  >





  setFilterData:

  React.Dispatch<

    React.SetStateAction<any[]>

  >





  setLoading:

  React.Dispatch<

    React.SetStateAction<boolean>

  >





  // TAMBAHAN
  // UNTUK REFRESH DATA PAGE

  setRefresh:

  React.Dispatch<

    React.SetStateAction<number>

  >



}







// ============================================================
// TABS
// ============================================================


const tabs = [


  {
    id:"availability",
    label:"Stock Availability",
  },


  {
    id:"trend",
    label:"Forecast Trend",
  },


  {
    id:"projection",
    label:"Inventory Projection",
  },


  {
    id:"recommendation",
    label:"Reorder Recommendation",
  },


  {
    id:"history",
    label:"History",
  },


]









// ============================================================
// COMPONENT
// ============================================================


export default function NavigationTabs({


  setForecastData,


  setFilterData,


  setLoading,


  setRefresh,


}:NavigationTabsProps){






// ============================================================
// ACTIVE TAB
// ============================================================


const [

activeTab,

setActiveTab

]

=

useState(

"availability"

)









// ============================================================
// UPLOAD MODAL
// ============================================================


const [

showUploadModal,

setShowUploadModal

]

=

useState(false)









// ============================================================
// UPLOAD TYPE
// ============================================================


const [

uploadType,

setUploadType

]

=

useState<

"GI"

|

"GR"

|

"stock"

|

null

>(null)









// ============================================================
// FILE INPUT
// ============================================================


const fileInputRef =


useRef<HTMLInputElement>(null)









// ============================================================
// OPEN MODAL
// ============================================================


function handleUploadClick(){


setShowUploadModal(true)


}









// ============================================================
// SELECT UPLOAD TYPE
// ============================================================


function chooseUploadType(


type:

"GI"

|

"GR"

|

"stock"


){



setUploadType(type)



setShowUploadModal(false)





setTimeout(()=>{


fileInputRef

.current

?.

click()



},100)



}









// ============================================================
// HANDLE FILE UPLOAD
// ============================================================


async function handleFileChange(



event:

React.ChangeEvent<HTMLInputElement>



){



const file =

event.target.files?.[0]





if(!file){


return


}









if(!uploadType){



alert(

"Jenis upload belum dipilih."

)



return



}









const formData =

new FormData()



formData.append(

"file",

file

)









try{



setLoading(true)









// ========================================================
// ENDPOINT
// ========================================================


let endpoint = ""








if(uploadType==="GI"){


endpoint =


"http://127.0.0.1:8001/api/upload-gi"


}







else if(uploadType==="GR"){


endpoint =


"http://127.0.0.1:8001/api/upload-gr"


}







else if(uploadType==="stock"){


endpoint =


"http://127.0.0.1:8001/api/upload-stock"


}









console.log(

"=============================="

)


console.log(

"UPLOAD DATA"

)


console.log(

"TYPE:",

uploadType

)


console.log(

"FILE:",

file.name

)


console.log(

"ENDPOINT:",

endpoint

)


console.log(

"=============================="

)








// ========================================================
// SEND FILE
// ========================================================


const response =


await fetch(


endpoint,


{


method:"POST",


body:formData,


}


)








if(!response.ok){



const errorText =


await response.text()





console.error(

"BACKEND ERROR:",

errorText

)





throw new Error(

`Upload gagal (${response.status})`

)



}








const result =


await response.json()






console.log(

"UPLOAD RESPONSE:",

result

)



// ========================================================
// UPDATE FILTER DATA
// ========================================================


if(



Array.isArray(

result.filter_data

)



){



setFilterData(

result.filter_data

)



}









// ========================================================
// REFRESH DASHBOARD
//
// TIDAK LANGSUNG SET DATA TABLE
//
// page.tsx yang bertugas mengambil:
// - /api/gi/latest
// - /api/gr/latest
// - /api/stock/latest
//
// ========================================================


setRefresh(

(prev)=>

prev + 1

)








alert(


`Data ${uploadType} berhasil diupload.`


)









}



catch(error){



console.error(

"UPLOAD ERROR:",

error

)






alert(



error instanceof Error


?


error.message


:


"Upload gagal."



)



}









finally{



setLoading(false)







setUploadType(null)








if(fileInputRef.current){


fileInputRef.current.value=""


}



}



}









// ============================================================
// RENDER
// ============================================================


return (


<div

className="

mb-6

"

>








{/* ======================================================
    NAVIGATION BAR
====================================================== */}



<div


className="

flex

h-16

items-center

justify-between

gap-4

rounded-[20px]

border

border-white/15

bg-white/10

px-6

shadow-[0_8px_24px_rgba(0,0,0,0.15)]

backdrop-blur-2xl

"


>









{/* ==================================================
    TAB MENU
================================================== */}



<div


className="

flex

min-w-0

items-center

gap-1

overflow-hidden

"


>



{


tabs.map(


(tab)=>(


<button


key={tab.id}


type="button"


onClick={()=>{



setActiveTab(

tab.id

)




console.log(

"ACTIVE TAB:",

tab.id

)



}}



className={`

relative

flex-shrink-0

whitespace-nowrap

px-4

py-2.5

text-[14px]

font-medium



${

activeTab===tab.id

?

"text-blue-400"

:

"text-white/65 hover:text-white"

}



`}



>


{

tab.label

}





{



activeTab===tab.id

&&



(



<span


className="

absolute

left-4

right-4

-bottom-[9px]

h-[2.5px]

rounded-full

bg-[#42A5FF]

"



/>



)



}



</button>



)



)



}



</div>









{/* ==================================================
    ACTION BUTTON
================================================== */}



<div


className="

flex

items-center

gap-2

"


>





<button


type="button"


onClick={handleUploadClick}



className="

flex

items-center

gap-2

rounded-xl

border

border-white/15

bg-white/10

px-3.5

py-2.5

text-[13px]

font-medium

text-white

transition-colors

hover:bg-white/15

"



>



<Download size={15}/>


Upload



</button>






</div>






</div>














{/* ======================================================
    UPLOAD MODAL
====================================================== */}



{



showUploadModal



&&



(



<div


className="

fixed

inset-0

z-50

flex

items-center

justify-center

bg-black/50

backdrop-blur-sm

"



>



<div


className="

w-[320px]

rounded-2xl

border

border-white/20

bg-[#111827]

p-6

shadow-xl

"



>





<h3


className="

mb-5

text-lg

font-semibold

text-white

"


>


Pilih Jenis Data


</h3>








<div


className="

flex

flex-col

gap-3

"



>






<button


type="button"


onClick={()=>chooseUploadType("GI")}



className="

rounded-xl

bg-white/10

px-5

py-3

text-white

transition-colors

hover:bg-blue-600/30

"


>


Data GI


</button>







<button


type="button"


onClick={()=>chooseUploadType("GR")}



className="

rounded-xl

bg-white/10

px-5

py-3

text-white

transition-colors

hover:bg-blue-600/30

"


>


Data GR


</button>







<button


type="button"


onClick={()=>chooseUploadType("stock")}



className="

rounded-xl

bg-white/10

px-5

py-3

text-white

transition-colors

hover:bg-blue-600/30

"


>


Stock Terkini


</button>








<button


type="button"


onClick={()=>{


setShowUploadModal(false)


setUploadType(null)



}}



className="

mt-2

text-sm

text-white/60

hover:text-white

"


>


Batal


</button>






</div>






</div>





</div>



)



}














{/* ======================================================
    FILE INPUT
====================================================== */}



<input


ref={fileInputRef}


type="file"


accept="

.xlsx,

.xls

"


className="hidden"



onChange={handleFileChange}



/>







</div>


)


}

