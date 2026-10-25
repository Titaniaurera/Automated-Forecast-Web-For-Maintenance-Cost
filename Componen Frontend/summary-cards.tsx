"use client"


import {

  CheckCircle,

  AlertTriangle,

  Zap,

  TrendingUp,

  Package

} from "lucide-react"





// ============================================================
// TYPE DATA
// ============================================================


interface ForecastItem {


  Material?: string



  "Material Description"?: string







  // =========================
  // COVERAGE
  // =========================


  Coverage?: number | null







  // =========================
  // STATUS
  // =========================


  Status?: string | null





}









// ============================================================
// PROPS
// ============================================================


interface SummaryCardsProps {


  data: ForecastItem[]


}












// ============================================================
// COMPONENT
// ============================================================


export function SummaryCards({


data


}:SummaryCardsProps){







// ============================================================
// VALIDASI DATA
// ============================================================


const items = Array.isArray(data)


?


data


:


[]














// ============================================================
// TOTAL MATERIAL
// ============================================================


const totalMaterial = items.length













// ============================================================
// STATUS COUNT
// ============================================================


// =========================
// AMAN
// =========================


const amanCount = items.filter(


(item)=>



item.Status === "Aman"



||



item.Status === "Normal"



||



item.Status === "Normal Stock"



).length











// =========================
// KRITIS
// =========================


const kritisCount = items.filter(


(item)=>


item.Status === "Kritis"



||



item.Status === "Stock Out Risk"



).length











// =========================
// REORDER
// =========================


const reorderCount = items.filter(


(item)=>


item.Status === "Reorder"



).length











// ============================================================
// COVERAGE
// ============================================================


const coverageData = items.filter(


(item)=>


item.Coverage !== null



&&



item.Coverage !== undefined



)









const averageCoverage =


coverageData.length > 0



?


coverageData.reduce(


(total,item)=>


total + Number(item.Coverage),


0


)

/

coverageData.length





:


null






// ============================================================
// FORMAT NUMBER
// ============================================================


const formatNumber = (

value:number | string | null

)=>{


if(

value === null

||

value === undefined

)

{


return "-"

}



return new Intl.NumberFormat(

"id-ID",

{

maximumFractionDigits:0

}

).format(

Number(value)

)


}











// ============================================================
// FORMAT COVERAGE
// ============================================================


const formatCoverage = (

value:number | null

)=>{


if(

value === null

||

value === undefined

)

{


return "-"

}



return value.toFixed(2)


}












// ============================================================
// CARD DATA
// ============================================================


const cards = [







// ============================================================
// TOTAL MATERIAL
// ============================================================


{


label:

"Total Material",



value:

formatNumber(

totalMaterial

),



icon:

Package,



iconStyle:

"bg-blue-500/10 text-blue-400"



},







// ============================================================
// AMAN
// ============================================================


{


label:

"Aman",



value:

formatNumber(

amanCount

),



icon:

CheckCircle,



iconStyle:

"bg-emerald-500/10 text-emerald-400"



},







// ============================================================
// KRITIS
// ============================================================


{


label:

"Kritis",



value:

formatNumber(

kritisCount

),



icon:

AlertTriangle,



iconStyle:

"bg-amber-500/10 text-amber-400"



},







// ============================================================
// REORDER
// ============================================================


{


label:

"Reorder",



value:

formatNumber(

reorderCount

),



icon:

Zap,



iconStyle:

"bg-red-500/10 text-red-400"



},







// ============================================================
// COVERAGE
// ============================================================


{


label:

"Rata-rata Coverage",



value:

formatCoverage(

averageCoverage

),



icon:

TrendingUp,



iconStyle:

"bg-sky-500/10 text-sky-400"



}



]

// ============================================================
// RETURN
// ============================================================


return (


<section


className="

grid

gap-4

grid-cols-1

sm:grid-cols-2

lg:grid-cols-5

"

>


{


cards.map((card)=>(



<div


key={card.label}


className="

group

relative

overflow-hidden

rounded-2xl

border

border-white/10

bg-[#102A57]/90

backdrop-blur-xl

p-5

shadow-[0_8px_20px_rgba(0,0,0,.18)]

transition-all

duration-300

hover:-translate-y-1

hover:border-blue-400/40

hover:shadow-[0_0_25px_rgba(59,130,246,.25)]

"



>


<div


className="

flex

items-center

justify-between

"



>


<span


className="

text-xs

font-medium

uppercase

tracking-wide

text-white/60

"



>


{card.label}


</span>







<div


className={`

grid

h-10

w-10

place-items-center

rounded-xl

${card.iconStyle}

`}



>


<card.icon

className="

h-5

w-5

"

/>


</div>







</div>









<p


className="

mt-4

text-3xl

font-semibold

tracking-tight

text-white

"



>


{card.value}


</p>









<p


className="

mt-2

text-xs

text-white/50

"



>


Mengikuti filter aktif


</p>






</div>




))


}



</section>


)


}
