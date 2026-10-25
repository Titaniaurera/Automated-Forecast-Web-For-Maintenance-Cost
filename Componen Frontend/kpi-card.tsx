"use client"


import {

  Package,

  CheckCircle,

  AlertTriangle,

  Zap,

  TrendingUp,

} from "lucide-react"









// ============================================================
// TYPE DATA
// ============================================================


interface ForecastItem {


  Material?: string



  "Material Description"?: string







  // =========================
  // STOCK
  // =========================


  Stock?: number | null







  // =========================
  // ACTUAL
  // =========================


  GI_Actual?: number | null



  GR_Actual?: number | null







  // =========================
  // FORECAST
  // =========================


  Forecast_GI?: number | null



  Forecast_GR?: number | null







  // =========================
  // PROJECTION
  // =========================


  Projected_Stock?: number | null



  Gap_Kebutuhan?: number | null







  // =========================
  // COVERAGE
  // =========================


  Coverage?: number | null



  Coverage_Projection?: number | null







  // =========================
  // STATUS
  // =========================


  Status?: string | null







  // =========================
  // NEW FILTER METADATA
  // =========================


  Has_GI?: boolean



  Has_GR?: boolean



  Has_Stock?: boolean



  History_Count?: number | null





}











// ============================================================
// PROPS
// ============================================================


interface KPICardsProps {


  data: ForecastItem[]


}












// ============================================================
// COMPONENT
// ============================================================


export default function KPICards({


data


}:KPICardsProps){







// ============================================================
// VALIDASI DATA
// ============================================================


const items = Array.isArray(data)

?

data

:

[]












// ============================================================
// REMOVE DUPLICATE MATERIAL
// ============================================================


const uniqueItems = Array.from(



new Map(


items.map(


(item,index)=>[



item.Material

??

`unknown-${index}`,



item



]


)


).values()



)













// ============================================================
// NORMALIZE DATA
// ============================================================


const calculatedData = uniqueItems.map(


(item)=>(


{


...item,





Coverage:

item.Coverage ?? null,





Status:

item.Status ?? null,







Has_GI:

item.Has_GI ?? false,





Has_GR:

item.Has_GR ?? false,





Has_Stock:

item.Has_Stock ?? false,





History_Count:

item.History_Count ?? 0





}


)


)

// ============================================================
// TOTAL MATERIAL
// ============================================================


const totalMaterial = calculatedData.length













// ============================================================
// MATERIAL DENGAN STATUS
// ============================================================


const stockAnalysisAvailable = calculatedData.filter(


(item)=>


item.Status !== null

&&

item.Status !== undefined

&&

item.Status !== ""



).length














// ============================================================
// MATERIAL DENGAN COVERAGE
// ============================================================


const coverageAvailable = calculatedData.filter(


(item)=>


item.Coverage !== null

&&

item.Coverage !== undefined



).length














// ============================================================
// STATUS COUNT
// ============================================================


// =========================
// AMAN
// =========================


const safeCount = calculatedData.filter(


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


const criticalCount = calculatedData.filter(


(item)=>


item.Status === "Kritis"

||

item.Status === "Stock Out Risk"



).length












// =========================
// REORDER
// =========================


const reorderCount = calculatedData.filter(


(item)=>


item.Status === "Reorder"



).length














// ============================================================
// AVERAGE COVERAGE
// ============================================================


const coverageValues = calculatedData


.filter(


(item)=>


item.Coverage !== null

&&

item.Coverage !== undefined



)


.map(


(item)=>

Number(

item.Coverage

)


)












const averageCoverage =



coverageValues.length > 0



?



coverageValues.reduce(


(total,value)=>


total + value,


0



)

/



coverageValues.length





:


null












// ============================================================
// PERCENTAGE
// ============================================================


const safePercentage =


stockAnalysisAvailable > 0



?



(

safeCount

/

stockAnalysisAvailable


)

*

100




:


0












const criticalPercentage =


stockAnalysisAvailable > 0



?



(

criticalCount

/

stockAnalysisAvailable


)

*

100




:


0












const reorderPercentage =


stockAnalysisAvailable > 0



?



(

reorderCount

/

stockAnalysisAvailable


)

*

100




:


0












// ============================================================
// FORMAT
// ============================================================


const formatNumber = (

value:number | null | undefined

)=>{


if(

value===null

||

value===undefined

)

{


return "-"

}



return new Intl.NumberFormat(

"id-ID",

{

maximumFractionDigits:0

}

).format(value)


}









const formatCoverage = (

value:number | null

)=>{


if(

value===null

||

value===undefined

)

{


return "-"

}



return value.toFixed(2)


}









const formatPercentage = (

value:number

)=>{


return `${value.toFixed(1)}%`


}


// ============================================================
// KPI DATA
// ============================================================


const kpiData = [





// ============================================================
// TOTAL MATERIAL
// ============================================================


{


id:"total",



title:"Total Material",



value:

formatNumber(

totalMaterial

),



subtitle:

"Material aktif",



icon:

Package,



iconColor:

"text-blue-400",



iconBg:

"bg-blue-500/10",



subtitleColor:

"text-white/70"



},









// ============================================================
// AMAN
// ============================================================


{


id:"safe",



title:"Aman",



value:

formatNumber(

safeCount

),



subtitle:


stockAnalysisAvailable > 0



?


`${

formatPercentage(

safePercentage

)

}

dari total`



:


"Menunggu data",



icon:

CheckCircle,



iconColor:

"text-emerald-400",



iconBg:

"bg-emerald-500/10",



subtitleColor:

"text-emerald-400"



},









// ============================================================
// KRITIS
// ============================================================


{


id:"critical",



title:"Kritis",



value:

formatNumber(

criticalCount

),



subtitle:


stockAnalysisAvailable > 0



?


`${

formatPercentage(

criticalPercentage

)

}

dari total`



:


"Menunggu data",



icon:

AlertTriangle,



iconColor:

"text-amber-400",



iconBg:

"bg-amber-500/10",



subtitleColor:

"text-amber-400"



},









// ============================================================
// REORDER
// ============================================================


{


id:"reorder",



title:"Reorder",



value:

formatNumber(

reorderCount

),



subtitle:


stockAnalysisAvailable > 0



?


`${

formatPercentage(

reorderPercentage

)

}

dari total`



:


"Menunggu data",



icon:

Zap,



iconColor:

"text-red-400",



iconBg:

"bg-red-500/10",



subtitleColor:

"text-red-300"



},









// ============================================================
// COVERAGE
// ============================================================


{


id:"coverage",



title:"Rata-rata Coverage",



value:


averageCoverage !== null



?


formatCoverage(

averageCoverage

)



:


"-",



subtitle:


coverageAvailable > 0



?


"Bulan"



:


"Menunggu data",



icon:

TrendingUp,



iconColor:

"text-sky-400",



iconBg:

"bg-sky-500/10",



subtitleColor:

"text-white/70"



}



]

// ============================================================
// RETURN
// ============================================================


return (



<div


className="

grid

grid-cols-1

gap-3

mb-6

md:grid-cols-2

xl:grid-cols-5

"



>


{



kpiData.map(


(kpi)=>{



const Icon = kpi.icon







return(



<div



key={kpi.id}



className="

group

rounded-[18px]

border

border-white/10

bg-[#102A57]/90

backdrop-blur-xl

px-5

py-4

shadow-[0_6px_18px_rgba(0,0,0,.18)]

transition-all

duration-300

ease-out

hover:-translate-y-1

hover:border-[#3B82F6]/60

hover:shadow-[0_0_25px_rgba(59,130,246,.35)]

"



>







<div



className="

flex

items-center

gap-3

"



>








<div



className={`

${kpi.iconBg}

w-11

h-11

rounded-full

flex

items-center

justify-center

shrink-0

transition-all

duration-300

group-hover:scale-110

`}



>



<Icon



className={`

w-5

h-5

${kpi.iconColor}

`}



/>



</div>









<div



className="

flex-1

"



>



<p



className="

text-[13px]

font-medium

text-white/75

"



>


{kpi.title}



</p>








<h2



className="

mt-2

text-[28px]

font-bold

leading-none

text-white

"



>


{kpi.value}



</h2>








<p



className={`

mt-2

text-[13px]

font-medium

${kpi.subtitleColor}

`}



>


{kpi.subtitle}



</p>







</div>







</div>






</div>





)


}



)



}





</div>





)


}


