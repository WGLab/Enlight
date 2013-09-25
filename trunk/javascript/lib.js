function response_to_select_region(input_value) {
    if (input_value=="snp") 
    {
	document.main.refsnp_table.style.visibility="visible";
    } else if (input_value=="gene")
    {
	document.main.refgene_table.style.visibility="visible";
    } else if (input_value=="chr")
    {
	document.main.chr_table.style.visibility="visible";
    }
}

