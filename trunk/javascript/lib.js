function response_to_select_region(input_value) {
	snp=document.getElementById('snp');
	gene=document.getElementById('gene');
	chr=document.getElementById('chr');
    if (input_value=="snp") 
    {
    	snp.style.display="block";
    	gene.style.display="none";
    	chr.style.display="none";
    } else if (input_value=="gene")
    {
    	gene.style.display="block";
    	snp.style.display="none";
    	chr.style.display="none";
    } else if (input_value=="chr")
    {
    	chr.style.display="block";
    	snp.style.display="none";
    	gene.style.display="none";
    }
}

