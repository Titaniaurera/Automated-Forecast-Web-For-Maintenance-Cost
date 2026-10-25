"use client"


import {

  ChevronDown,
  Search,
  List,
  Grid3x3,
  Check

} from "lucide-react"


import {

useState

} from "react"


import type {

Dispatch,
SetStateAction

} from "react"




// ============================================================
// TYPE
// ============================================================


type MaterialFilters = {

  availableGI_GR:boolean

  availableGI_GR_STOCK:boolean

  historyGT7:boolean

}





interface FilterSectionProps {


materialFilters:MaterialFilters


setMaterialFilters:

Dispatch<

SetStateAction<MaterialFilters>

>





searchTerm:string


setSearchTerm:

Dispatch<

SetStateAction<string>

>





mrpControllerFilter:string


setMrpControllerFilter:

Dispatch<

SetStateAction<string>

>


mrpControllerOptions:string[]





storageLocationFilter:string


setStorageLocationFilter:

Dispatch<

SetStateAction<string>

>


storageLocationOptions:string[]





materialTypeFilter:string


setMaterialTypeFilter:

Dispatch<

SetStateAction<string>

>


materialTypeOptions:string[]





statusFilter:string


setStatusFilter:

Dispatch<

SetStateAction<string>

>


}







// ============================================================
// COMPONENT
// ============================================================


export default function FilterSection({

materialFilters,

setMaterialFilters,


searchTerm,

setSearchTerm,


mrpControllerFilter,

setMrpControllerFilter,

mrpControllerOptions,


storageLocationFilter,

setStorageLocationFilter,

storageLocationOptions,


materialTypeFilter,

setMaterialTypeFilter,

materialTypeOptions,


statusFilter,

setStatusFilter,


}:FilterSectionProps){





const [

viewMode,

setViewMode

]=useState<"list"|"grid">("list")





const [

openDropdown,

setOpenDropdown

]=useState<string>("")






const statusOptions=[

"Semua Status",

"Normal Stock",

"Stock Out Risk",

"Overstock Risk"

]







function toggleMaterial(

key:keyof MaterialFilters

){


setMaterialFilters(prev=>({

...prev,

[key]:

!prev[key]

}))


}







function closeDropdown(){


setOpenDropdown("")


}






function Dropdown({

title,

value,

options,

defaultValue,

onChange,

id


}:{

title:string

value:string

options:string[]

defaultValue:string

onChange:(v:string)=>void

id:string

}){


return(

<div className="relative">


<label className="
mb-2
block
text-[12px]
font-medium
text-white/60
">

{title}

</label>





<button

type="button"

onClick={()=>{


setOpenDropdown(

openDropdown===id

?

""

:

id

)


}}

className="
flex
h-10
w-full
items-center
justify-between
rounded-xl
border
border-white/10
bg-[#0B2148]
px-4
text-sm
text-white
"

>


<span className="truncate">

{value}

</span>



<ChevronDown className="h-4 w-4"/>


</button>





{

openDropdown===id &&

(

<div className="
absolute
top-[72px]
z-50
w-full
overflow-hidden
rounded-xl
border
border-white/10
bg-[#0B2148]
shadow-xl
">


<button

type="button"

onClick={()=>{

onChange(defaultValue)

closeDropdown()

}}

className="
w-full
px-4
py-3
text-left
text-sm
text-white
hover:bg-white/10
"

>

{defaultValue}

</button>





{

options.map(item=>(


<button

key={item}

type="button"

onClick={()=>{


onChange(item)

closeDropdown()


}}

className="
w-full
px-4
py-3
text-left
text-sm
text-white/80
hover:bg-white/10
"

>

{item}

</button>


))

}



</div>

)

}




</div>

)

}

return(

<div

className="
rounded-[18px]
border
border-white/10
bg-[#102A57]/90
backdrop-blur-xl
shadow-[0_8px_20px_rgba(0,0,0,.18)]
p-5
mb-6
"

>





{/* MATERIAL FILTER + DROPDOWN */}

<div

className="
grid
grid-cols-1
gap-4
md:grid-cols-2
xl:grid-cols-5
"

>




{/* MATERIAL FILTER */}


<div>


<label className="
mb-2
block
text-[12px]
font-medium
text-white/60
">

Material Filter

</label>




<div className="
rounded-xl
border
border-white/10
bg-[#0B2148]
p-3
space-y-2
">





<button

type="button"

onClick={()=>{


setMaterialFilters({

availableGI_GR:false,

availableGI_GR_STOCK:false,

historyGT7:false

})


}}

className="
flex
items-center
gap-2
text-sm
text-white
"

>

<div className={`
h-4
w-4
rounded
border
flex
items-center
justify-center

${
!materialFilters.availableGI_GR &&
!materialFilters.availableGI_GR_STOCK &&
!materialFilters.historyGT7

?

"bg-blue-600 border-blue-500"

:

"border-white/30"

}

`}>

{

!materialFilters.availableGI_GR &&
!materialFilters.availableGI_GR_STOCK &&
!materialFilters.historyGT7

&&

<Check className="h-3 w-3"/>

}

</div>


All Material


</button>









<button

type="button"

onClick={()=>toggleMaterial("availableGI_GR")}

className="
flex
items-center
gap-2
text-sm
text-white
"

>

<div className={`
h-4
w-4
rounded
border
flex
items-center
justify-center

${
materialFilters.availableGI_GR

?

"bg-blue-600 border-blue-500"

:

"border-white/30"

}

`}>

{

materialFilters.availableGI_GR

&&

<Check className="h-3 w-3"/>

}

</div>


Available GI + GR


</button>










<button

type="button"

onClick={()=>toggleMaterial("availableGI_GR_STOCK")}

className="
flex
items-center
gap-2
text-sm
text-white
"

>

<div className={`
h-4
w-4
rounded
border
flex
items-center
justify-center

${
materialFilters.availableGI_GR_STOCK

?

"bg-blue-600 border-blue-500"

:

"border-white/30"

}

`}>

{

materialFilters.availableGI_GR_STOCK

&&

<Check className="h-3 w-3"/>

}

</div>


Available GI + GR + Stock


</button>










<button

type="button"

onClick={()=>toggleMaterial("historyGT7")}

className="
flex
items-center
gap-2
text-sm
text-white
"

>

<div className={`
h-4
w-4
rounded
border
flex
items-center
justify-center

${
materialFilters.historyGT7

?

"bg-blue-600 border-blue-500"

:

"border-white/30"

}

`}
>

{


materialFilters.historyGT7

&&

<Check className="h-3 w-3"/>

}

</div>


History &gt; 7


</button>






</div>


</div>










<Dropdown

title="MRP Controller"

value={mrpControllerFilter}

options={mrpControllerOptions}

defaultValue="Semua MRP Controller"

id="mrp"

onChange={setMrpControllerFilter}

/>





<Dropdown

title="Storage Location"

value={storageLocationFilter}

options={storageLocationOptions}

defaultValue="Semua Storage Location"

id="storage"

onChange={setStorageLocationFilter}

/>





<Dropdown

title="Material Type"

value={materialTypeFilter}

options={materialTypeOptions}

defaultValue="Semua Material Type"

id="material"

onChange={setMaterialTypeFilter}

/>





<Dropdown

title="Status"

value={statusFilter}

options={statusOptions}

defaultValue="Semua Status"

id="status"

onChange={setStatusFilter}

/>




</div>









{/* SEARCH + VIEW */}


<div

className="
mt-5
flex
items-center
gap-3
"

>




<div className="
relative
flex-1
">


<Search

className="
absolute
left-4
top-1/2
h-4
w-4
-translate-y-1/2
text-white/40
"

/>




<input


type="text"


value={searchTerm}


onChange={(e)=>setSearchTerm(e.target.value)}


placeholder="Cari material / deskripsi..."


className="
h-10
w-full
rounded-xl
border
border-white/10
bg-[#0B2148]
pl-11
text-sm
text-white
placeholder:text-white/40
outline-none
"




/>


</div>










<div className="flex gap-2">


<button

type="button"

onClick={()=>setViewMode("list")}


className={`

flex
h-10
w-10
items-center
justify-center
rounded-xl
border

${
viewMode==="list"

?

"bg-blue-600 border-blue-500 text-white"

:

"bg-[#0B2148] border-white/10 text-white/60"

}

`}

>


<List className="h-5 w-5"/>


</button>






<button

type="button"

onClick={()=>setViewMode("grid")}


className={`

flex
h-10
w-10
items-center
justify-center
rounded-xl
border

${
viewMode==="grid"

?

"bg-blue-600 border-blue-500 text-white"

:

"bg-[#0B2148] border-white/10 text-white/60"

}

`}

>


<Grid3x3 className="h-5 w-5"/>


</button>





</div>




</div>








</div>


)


}


