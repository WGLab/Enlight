#!/usr/bin/Rscript --vanilla 
# --default-packages=utils,stats,lattice,grid,getopts
# need to check if the line above works on the web deployment machine.

# Copyright 2010 Randall Pruim, Ryan Welch
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

require(stats);
require(utils);
require(grid);
require(lattice);
require(methods);

omittedGenes <- character(0);     # will be set in gobalenv()
warningMessages <- character(0);  # will be set in gobalenv()

################################################################################################
# function definitions
################################################################################################

################################################################################
#
# takes string and converts '' and 'null' (case insensitive) to NULL, else unchanged.
#
as.filename <- function(x) {
    if (! is.character(x) || toupper(x) == toupper('null') || x == '') {
	return(NULL)
    } else {
	return(x)
    }
}

################################################################################
#
# modify column names the way R does
#
char2Rname <- function(x) {
    x <- gsub('-','.',x);
    x <- gsub('=','.',x);
    x <- gsub('\ ','.',x);
    return(x)
}

################################################################################
#
# build a factor
#
MakeFactor <- function(x,levels,na.level=NA) {


    f <- factor(x, levels=levels)
    if (any( is.na(f))){
	levels(f) <- c(levels(f),na.level)
	f[ is.na(f) ] <- na.level
    }
    return(f)
}

################################################################################
#
# pretty print scientific notation from log10(x)
#
log2sci <- function(x) {
    # write x as 10^(e) * 10^r where e is an integer and r is in [0,1)
    e <- floor(x)
    r <- x - e
    m <- 10^(r)
    return(paste(format(m,digits=3),"E",e,sep=""));
}

################################################################################
#
# Sniff a vector to see if it smells
#
Sniff <- function(vec,type=c('snp'),n=10) {
    n <- min(n,length(vec))
    type <- match.arg(type)

    if (type == 'snp') {
	yes <- union(union(
			   grep('rs',vec[1:n]), 
			   grep('chr[[:digit:]]+:[[:digit:]]',vec[1:n])),
		     grep('chr[[:alpha:]]+:[[:digit:]]',vec[1:n])
		     )
	if ( length(yes) == n ) return (TRUE)
	return(FALSE)
    }
    return(FALSE)
}

################################################################################
#
# Which side should legend go on?
#
AutoLegendSide <- function(pval,pos,posRange = range(pos)) {
    M <- .5 * max(pval);
    left <- min(pos[pval > M]);
    right <- max(pos[pval > M]);
    mid <- mean(posRange);
    if ( (mid - left) > (right - mid) ) { 
	return ('right'); 
    }
    return('left');
}

################################################################################
#
# choose a transformation for p-values
#
SetTransformation <- function(mn,mx,alreadyTransformed=FALSE) {
    if (alreadyTransformed) { return ( function(x){x} ) }
    if (mx > 1)  { return( function(x) {x} ) }  # assume -log10 transform has already been applied
    if (mn < 0)  { return( function(x) {-x} ) } # assume log10 transform has already been applied
    return ( function(x) {-log10(x)} )
}

################################################################################
#
# Set titles correctly for D' and r^2
#
SetLDTitle <- function(col,title) {
    if ( col == 'dprime' & is.null(title) ) { return ("D'"); }
    if ( col == 'rsquare' & is.null(title) ) { return (expression(r^2)); }
    if (is.null(title)) { return (""); }
    return(title);
}

################################################################################
#
# extends default modifyList so that it handles NULL values in list differently.
#
ModifyList <- function (x, val, replaceWithNull = FALSE) 
{
    stopifnot(is.list(x), is.list(val));
    xnames <- names(x);
    for (v in names(val)) {
	if (v %in% xnames && is.list(x[[v]]) && is.list(val[[v]])) {
	    x[[v]] <- ModifyList(x[[v]], val[[v]], replaceWithNull=replaceWithNull);
	} else {
	    if (!is.null(val[[v]]) || replaceWithNull) {
		x[[v]] <- val[[v]];
	    }
	}
    }
    return(x);
}

################################################################################
#
# like lapply but on a subset of a list; rest of list unchanged.
#

sublapply <- function(x,names=names(x),fun) {

    fun <- as.function(fun);

    for (name in names) {
	if (! is.null(x[[name]] ) ) {
	    x[[name]] <- fun(x[[name]]);
	}
    }
    return(x);
}

################################################################################
#
# like modifyList, but works when names of val are unique prefixes of names of x
#
ConformList <- function(x,names,case.sensitive=FALSE,message=FALSE) {

    own.ind <- 0;
    for (name in names(x)) {
	own.ind <- own.ind + 1;
	if (case.sensitive) {
	    match.ind <- pmatch( name, names );
	} else {
	    match.ind <- pmatch( toupper(name), toupper(names) );
	}
	if (! is.na(match.ind)) {
	    names(x)[own.ind] <- names[match.ind];
	} else {
	    if (! is.null(message) ) { message(paste("No unique match for ",name,"=",x[[own.ind]],sep="")); }
	}
    }
    return(x);
}

################################################################################
#
# like modifyList, but works when names of val are unique prefixes of names of x
#
PModifyList <- function(x,val,...) {
    ModifyList(x,ConformList(val,names(x),...));
}

################################################################################
#
# Modify the list args according to the value of theme
#
ProcessOneTheme <- function(args,theme) {
    if ( is.character(theme) ){
	theme=paste(theme,'.theme',sep='')
	return( do.call(theme,list(args=args)) )
    }
    return(args)
}

################################################################################
#
# process a list of themes in order
#
ProcessThemes <- function(args,themeString) {
    if (!is.character(themeString)) { return(args) }

    for (theme in unlist(strsplit(themeString,",")) ){
	args <- ProcessOneTheme(args,theme)
    }
    return(args)
}

################################################################################
#
# Some themes
#
ryan.theme <- function(args) {

    argUpdates <- list(
		       snpset=NULL,
		       format="pdf",
		       refDot=NULL,
		       geneFontSize=1.1,
		       categoryFontSize=1.1,
		       refsnpTextSize=1.5,
		       axisTextSize=1.45,
		       legendSize=1,
		       legendFrameAlpha=0,
		       legendAlpha=0,
		       axisSize=1.45,
		       recombPos=3, 
		       xlabPos=-2.75,
		       height=9,
		       rfrows=4,
		       genericRows=3,
		       xyplotRows=3
		       )
    return(ModifyList(args,argUpdates));
}

publication.theme <- ryan.theme;
pub.theme <- ryan.theme;

black.theme <- function(args) {
    argUpdates <- list(
		       axisTextColor='black',
		       rugColor='black',
		       frameColor='black'
		       )
    return(ModifyList(args,argUpdates));
}

giant.theme <-  function(args) {
    argUpdates <- list(
		       rfrows=10,
		       genericRows=7,
		       xyplotRows=5,
		       recombOver=TRUE,
		       recombAxisColor='black',
		       recombAxisAlpha=1,
		       legend='auto',
		       showAnnot=TRUE,
		       showRefsnpAnnot=FALSE,
		       annotPch='25,21,21,21,21,21,24,24,24',
		       recombColor='cyan',
		       ldColors='gray50,blue,green,yellow,orange,red,purple3'
		       )

    args <- ryan.theme(args);
    args <- black.theme(args);
    args <- ModifyList(args,argUpdates);
    return(args);
}
#############################################################
#
# Remove temporary files (used in final clean-up)
#
RemoveTempFiles <- function (...) {
    l <- list(...);
    removedFiles <- list();

    if (length(l) < 1) { return(removedFiles); }

    method <- unlist(lapply(l,function(x) { attr(x,"method") }));
    file <- unlist(lapply(l,function(x) { attr(x,"file") }));
    for (i in 1:length(method)) {
	if (method[i] == 'pquery') { file.remove( file[i] ); }
	removedFiles <- c(removedFiles, file[i]);
    }

    return(removedFiles); 
}

#############################################################
#
# Cleaning up at the end
#
CleanUp <- function(args,...) {
    if (args[['clean']]) {
	message("\nCleaning up.  The following files are begin removed: ");
	files <- RemoveTempFiles(...);
	message(paste("\t",files,"\n"));
	invisible(files);
    }
}

#############################################################
#
# Obtain data.  Data can be specified using a file.  When
# pquery is not available, this version will ignore the command
# and return default data if the file is missing.
#

GetDataFromFileIgnoreCommand <- function(file, default=data.frame(), clobber=FALSE, verbose=TRUE,...) {
    method <- "file";
    if (is.null(file)) {
	return(default)
    }
    if ( !file.exists(file) ) { 
	# warning(paste("Missing file:",file)) 
	return(default)
    }

    results <-  read.file(file,...) ;
    attr(results, "file") <- file;
    attr(results, "method") <- method;
    return(results);
}

#############################################################
#
# return an empty data from with some additonal attributes
#
empty.data.frame <- function(
			     file="none",command="none", method="empty.data.frame") {

    result <- data.frame();
    attr(result, "file") <- file;
    attr(result, "command") <- command;
    attr(result, "method") <- method;
}


#############################################################
#
# This is used to clone values from user specified arguemnts 
# to other arguments that the user did not set.  
# 
MatchIfNull <- function(args,toupdate,updatewith) {
    if ( is.null(args[[toupdate]]) ) {
	args[[toupdate]] <- args[[updatewith]]
    }
    return(args)
}

#############################################################
#
# All arguments are passed in with mode character (i.e., as strings)
# This functions converts arguments to the correct mode for
# internal use.
#
AdjustModesOfArgs <- function(args) {
    args <- sublapply(args,
		      c('legendAlpha', 'width','height',
			'frameAlpha','hiAlpha','rugAlpha',
			'refsnpLineAlpha', 'recombFillAlpha','recombLineAlpha', 'refsnpTextAlpha',
			'ymin','ymax','legendSize','refsnpTextSize','axisSize','axisTextSize','geneFontSize','categoryFontSize','smallDot',
			'largeDot','refDot'),
		      as.numeric);
    #generic mark
    args <- sublapply(args,
		      c('metal','recomb','ld','refSnpPosFile','snpsetFile','annot','refFlat','generic'),
		      as.filename);

    args <- sublapply(args,
		      c('chr','unit','xnsmall'),
		      as.integer);

    args <- sublapply(args,
		      c('experimental','clobber','recombOver','recombFill',
			'showRecomb','showGeneric','showAnnot','showRefsnpAnnot','bigDiamond','showPartialGenes','shiftGeneNames',
			'clean', 'dryRun','legendMissing'),
		      as.logical);

    args <- sublapply( args,
		      c('ldCuts','ldCutsForBarchart','xat','yat','annotPch'),
		      function(x) { as.numeric(unlist(strsplit(x,","))) } );

    args <- sublapply( args,
		      c('rfrows','genericRows','xyplotRows'),
		      function(x) { as.integer(unlist(strsplit(x,","))) } );

    args <- sublapply( args,
		      c('ldColors', 'ColorsForBarchart','format', 'annotOrder'),
		      function(x) { unlist(strsplit(x,",")) } );

    return(args);
}

#############################################################
#
# Returns text description of unit along chromosome depending
# on value of unit where unit is a number of base pairs
#
unit2char <- function(unit) {
    if (unit == 1000000) { return ("(Mb)"); }
    if (unit == 1000) { return ("(Kb)"); }
    return("");
}

#############################################################
#
# convert position that might include mb, kb into a base pair position
#
pos2bp <- function(pos) {
    unit<-1;
    posN <- as.character(pos);
    if (regexpr("kb",posN,ignore.case=TRUE) > 0) {
	unit <- 1000;
	posN <- sub("kb","",posN, ignore.case=T);
    }
    if (regexpr("mb",posN,ignore.case=TRUE) > 0) {
	unit <- 1000000;
	posN <- sub("mb","",posN, ignore.case=T);
    }
    #	message(paste('posN = ',posN, "  unit = ", unit));
    return( as.numeric(posN) * unit);
}

#############################################################
#
# read file, using filename to determine method.
#

read.file <- function(file,header=T,na.strings=c('NA','','.','na'),quote="",fill=TRUE,check.names=FALSE,...) 
{
    if (! file.exists(file) ) { 
	return(NULL);
	message(paste("Missing file: ", file));
    }

    # if file ends .csv, then read.csv
    if ( regexpr("\\.csv",file) > 0 ) {
	return(read.csv(file,header=header,na.strings=na.strings,quote=quote,fill=fill,check.names=check.names,...));
    }

    # if file ends .Rdata, then load
    if ( regexpr("\\.Rdata",file) > 0 ) {
	varName <- load(file);
	return(varName);
    }

    # default is read.table, force \t delimiter for all files except .csv
    return(read.table(file,header=header,na.strings=na.strings,quote=quote,fill=fill,sep="\t",check.names=check.names,...));
}

#############################################################
#
# write file, using filename to determine method.
#

write.file <- function(x, file, append=FALSE, clobber=TRUE, na='NA') {
    if (file.exists(file) && ! clobber && !append ) { 
	return(NULL);
	message(paste("File already exists: ", file));
    }

    # if file ends .csv, then write.csv
    if ( regexpr("\\.csv",file) > 0 ) {
	return(write.csv(x,file,append=append));
    }

    # if file ends .Rdata, then load
    if ( regexpr("\\.Rdata",file) > 0 ) {
	return(save.csv(x,file));
    }

    # default is read.table
    return(write.table(x,file,append=append));
}

#############################################################
#
# Converter from chrom (e.g., chr13) to chr (e.g., 13) format
#
chrom2chr <- function (x) {
    y <- substring(x,first=4);
    y[y=='X'] = '23';
    y[y=='Y'] = '24';
    y[y=='mito'] = '25';
    y[y=='XY'] = '26';
    as.numeric(y);
}

#############################################################
#
# Converter from chr (e.g., 13) to chrom (e.g., chr13) format
#
chr2chrom <- function (x) {
    if (x == 23 ) { return("chrX"); }
    if (x == 24 ) { return("chrY"); }
    if (x == 25 ) { return("mito"); }
    if (x == 26 ) { return("chrXY"); }
    return (paste("chr",as.numeric(x),sep=""));
}


#############################################################
#
# Linearly rescale values to fit in interval 
# If all values are equal, then return a vector the same length as x
# with all values set to constant (by default the larger end of the interval).
#
rescale <- function(x, original=c(min(x),max(x)), transformed = c(0,1) ){

    if ( length(transformed) != 2 || ! is.numeric(transformed) ||
	length(original) != 2 || ! is.numeric(original) ) 
    { return (x); }

    a <- original[1]; b <- original[2];
    u <- transformed[1]; v <- transformed[2];

    r <- v - (b-x)/(b-a) * (v-u);
    r[r < u] <- u;
    r[r > v] <- v;
    return(r);
}

#############################################################
#
# Flatten information originally in UCSC bed format.
# Tailored to fit nominclature and formatting used in files
# generated by Peter Chines.
#

flatten.bed <- function(x,multiplier=.001) {

    if (prod(dim(flatten.bed)) == 0) {
	df <- data.frame(
			 chrom  = c("chr0","chr0","chr0"),
			 chr    = c(0,0,0),
			 start= c(0,0,0),
			 stop = c(2,2,2),
			 type = c(0,2,1),
			 name = c('none','none','none'),
			 nmName = c('none','none','none'),
			 strand = c('+','+','+')
			 );
	return(df);
    }

    x$geneName <- as.character(x$geneName);
    x$name <- as.character(x$name);
    x$strand <- as.character(x$strand);
    lx <- dim(x)[1];

    blockStart <- unlist(lapply(
				strsplit(as.character(x$exonStarts),split=','),
				as.numeric));
    blockEnd <- unlist(lapply(strsplit(as.character(x$exonEnds),split=',')
			      ,
			      as.numeric));
    blockSize = blockEnd - blockStart;
    nameDup = rep(x$geneName,times=x$exonCount);
    nmNameDup = rep(x$name,times=x$exonCount);
    startDup = rep(x$txStart,times=x$exonCount);
    stopDup = rep(x$txEnd,times=x$exonCount);
    chromDup = rep(x$chrom,times=x$exonCount);
    strandDup = rep(x$strand,times=x$exonCount);

    # types: 
    # 0 = txStart to txEnd      (transcription region)
    # 1 = exonStart to exonEnd  (exons) 
    # 2 = cdsStart to cdsEnd    (coding region)

    df <- data.frame(
		     chrom  = c(x$chrom, x$chrom, chromDup),
		     chr = chrom2chr(c(x$chrom, x$chrom, chromDup)),
		     start= c(x$txStart, x$cdsStart, blockStart),
		     stop = c(x$txEnd, x$cdsEnd, blockEnd ),
		     type = c(rep(0,lx),rep(2,lx), rep(1,length(startDup))),
		     name = c(x$geneName, x$geneName, nameDup),
		     nmName = c(x$name, x$name, nameDup),
		     strand = c(x$strand, x$strand, strandDup)
		     );

    df$start <- df$start * multiplier;
    df$stop <- df$stop * multiplier;

    invisible(df);
}


#############################################################
#
# display reference SNP name and vertical line
#
grid.refsnp <- function(name,pos) {

    grid.text(as.character(name),x=unit(pos,"native"), y=unit(.95,'npc'), just=c("center","top"),
	      gp=gpar(cex=args[['refsnpTextSize']],col=args[['refsnpTextColor']],alpha=args[['refsnpTextAlpha']])
	      );
    grid.segments(
		  x0=unit(pos,"native"),
		  x1=unit(pos,"native"),
		  y0=unit(0,"npc"),
		  y1=unit(1,'npc') - unit(1.5,"lines"),
		  gp=gpar(
			  col=args[['refsnpLineColor']],
			  lwd=2,
			  alpha=args[['refsnpLineAlpha']])
		  );
}

#############################################################
#
# calculte width of text
#
textWidth <- function(text="",gp=gpar()) {
    return ( grobWidth(textGrob(text,gp=gp)) );
}

#############################################################
#
# generate text with arrow (or just compute width of same)
# this is a bit crude and clunky
#
arrowText <- function(text,x=unit(.5,'npc'), y=unit(.5,'npc'), direction='+',name=NULL,gp=gpar(),
		      check.overlap=TRUE, widthOnly=FALSE) {
    tWidth <- textWidth(text,gp)
    aWidth <- textWidth('xx,',gp)
    if (widthOnly) { return( convertWidth(tWidth + aWidth),unitTo='inches',valueOnly=TRUE ) }
    cWidth <- .1 * textWidth(',',gp)
    if ( direction %in% c('+','forward','->','>','right') ) {
	mult = 1
    } else {
	mult = -1
    }

    tg <- textGrob(text,
		   x=x - mult * .5 * aWidth, y=y,
		   check.overlap=check.overlap,
		   gp=gp,
		   name="label")
    ag <- linesGrob(  
		    x = unit.c( x - mult * .5 * aWidth  +  .5 * mult * tWidth + mult * unit(.005,'npc'), 
			       x + mult * .5 * aWidth  +  .5 * mult * tWidth ) ,
		    y=unit.c(y,y),
		    name="arrow",
		    #gp=gp,
		    arrow=arrow(type='open',
				angle=20,
				length=.75 * textWidth('x')
				)
		    )
    rect1 <- rectGrob(x=x - .5 * mult * aWidth, y=y, width=tWidth, height=.1);
    rect2 <- rectGrob(x=x + .50 * mult * tWidth, y=y, width=aWidth, height=.1,gp=gpar(col="red"));

    result <- gTree(children=gList(tg,ag),name=name)
    attr(result,'width') <- convertX(tWidth + aWidth,'inches')
    attr(result,'twidth') <- convertX(grobWidth(tg),'inches')
    attr(result,'awidth') <- convertX(grobWidth(ag),'inches')
    attr(result,'cWidth') <- cWidth
    attr(result,'tWidth') <- tWidth
    attr(result,'aWidth') <- aWidth
    return(result)
}

#############################################################
#
# hilite a particular region on the plot
#
panel.hilite <- function(range=c(lo,hi),lo,hi,col="transparent",fill="blue",alpha=.1){
    grid.rect( x=unit(range[1],"native"),width=unit(range[2]-range[1],"native"),
	      hjust=0,
	      gp=gpar(fill=fill,col=col, alpha=alpha)
	      );
}


#############################################################
#
# ribbonLegend from RGraphics example
#
ribbonLegend <- function (nlevels = NULL, breaks = NULL, cols, 
			  scale = range(breaks), 
			  margin = unit(0.5, "lines"), gp = NULL, vp = NULL, name = NULL) 
{
    gTree(nlevels = nlevels, breaks = breaks, cols = cols, scale = scale, 
	  children = ribbonKids(nlevels, breaks, cols, scale), 
	  childrenvp = ribbonVps(nlevels, breaks, margin, scale), 
	  gp = gp, vp = vp, name = name, cl = "ribbonLegend")
}

widthDetails.ribbonLegend <- function (x) 
{
    sum(layout.widths(viewport.layout(x$childrenvp[[1]])))
}

calcBreaks <- function (nlevels, breaks, scale) 
{
    if (is.null(breaks)) {
	seq(min(scale), max(scale), diff(scale)/nlevels)
    }
    else {
	breaks
    }
}

ribbonVps <- function (nlevels, breaks, margin, scale) 
{
    breaks <- format(signif(calcBreaks(nlevels, breaks, scale), 
			    3))
    vpTree(viewport(name = "layout", layout = grid.layout(3, 
							  4, widths = unit.c(margin, unit(1, "lines"), max(unit(0.8, 
														"lines") + stringWidth(breaks)), margin), heights = unit.c(margin, 
									     unit(1, "null"), margin))), vpList(viewport(layout.pos.col = 2, 
						   layout.pos.row = 2, yscale = scale, name = "ribbon"), 
													   viewport(layout.pos.col = 3, layout.pos.row = 2, yscale = scale, 
														    name = "labels")))
}

ribbonKids <- function (nlevels, breaks, cols, scale) 
{
    breaks <- calcBreaks(nlevels, breaks, scale)
    nb <- length(breaks)
    tickloc <- breaks[-c(1, nb)]
    gList(rectGrob(y = unit(breaks[-1], "native"), height = unit(diff(breaks), 
								 "native"), just = "top", gp = gpar(fill = cols), vp = vpPath("layout", 
								 "ribbon")), segmentsGrob(x1 = unit(0.5, "lines"), y0 = unit(tickloc, 
    "native"), y1 = unit(tickloc, "native"), vp = vpPath("layout", 
    "labels")), textGrob(x = unit(0.8, "lines"), y = unit(tickloc, 
    "native"), just = "left", label = format(signif(tickloc, 
						    3)), vp = vpPath("layout", "labels")))
}


#############################################################
#
# make a "list" of genes in flat.  returns a data frame
#
make.gene.list <-  function (flat, showIso=TRUE, subset, unit, ...) 

{       
    if ( prod(dim(flat)) <= 0 ) { return(NULL); }

    df <- flat;

    if (!missing(subset)) { df <- df[subset, ] }

    if ( prod(dim(flat)) <= 0 ) { return(NULL); }

    if (args[['showIso']]) {
	df$idnum <- match(df$nmName,unique(df$nmName));
    } else {
	df$idnum <- match(df$name,unique(df$name));
    }

    df0 <- df[df$type == 0, ];
    df1 <- df[df$type == 1, ];
    df2 <- df[df$type == 2, ];

    if ( "col" %in% names(df0) ) {
	col = df0$col
	fill = df0$col
    }

    return( data.frame(id=df0$idnum, gene=df0$name, chrom=df0$chrom, start=df0$start, stop=df0$stop,
		       startbp=df0$start * unit, stopbp=df0$stop*unit ) );
}

#############################################################
#
# display genes taking data from flattened bed format
#
panel.flatbed <-  function (x=NULL, y=NULL, flat, fill = "navy", col = "navy", alpha = 1, textcol='black',
			    multiplier = 0.001, height = 2/14, buffer=0.003, subset, cex=.9, rows=2, showPartialGenes=FALSE,
			    shiftGeneNames=TRUE,
			    computeOptimalRows=FALSE, ...) 

{      
    if ( prod(dim(flat)) <= 0 ) { return(1); }

    df <- flat;

    if (!missing(subset)) { df <- df[subset, ] }

    df$width <- df$stop - df$start;

    if (args[['showIso']]) {
	df$idnum <- match(df$nmName,unique(df$nmName));
    } else {
	df$idnum <- match(df$name,unique(df$name));
    }

    df0 <- df[df$type == 0, ];
    df1 <- df[df$type == 1, ];
    df2 <- df[df$type == 2, ];  # unused?

    if ( "col" %in% names(df0) ) {
	col = df0$col
	fill = df0$col
    }

    # removed duplicate idnums from df0
    df0 <- df0[order(df0$idnum),]     # sort to make sure repeated ids are adjacent
    df0$new <- c(1,diff(df0$idnum))  # identify new (1) vs. repeated (0)
    df0 <- df0[order(df0$idnum),]    # put back into original order
    df0uniq <- df0[df0$new == 1,]


    # determine the row to use
    maxIdnum <- max(c(0,df$idnum))
    rowUse <- rep(-Inf,1+maxIdnum)
    id2row <- rep(0,1+maxIdnum)      # keep track of locations for each gene


    # conversion to 'native' isn't working, so we convert evertyhing via inches to npc below.	
    # conversion utility

    native2npc <- function(x) {
	w <- diff(current.viewport()$xscale)
	a <- current.viewport()$xscale[1]
	return( (x-a) / w )
    }

    for (i in 1:dim(df0uniq)[1]) {
	cat(paste(i,": ",df0uniq$name[i],"\n"));
	leftGraphic <- native2npc(min(df$start[df$idnum == df0uniq$idnum[i]]))
	rightGraphic <- native2npc(max(df$stop[df$idnum == df0uniq$idnum[i]]))
	centerGraphic<- mean(c(leftGraphic,rightGraphic))
	at <- arrowText(df0uniq$name[i],
			x = unit((df0uniq$start[i] + df0uniq$stop[i])/2, 'native'),
			y = unit(0,'npc'), 
			direction = df0uniq$strand[i],
			check.overlap = TRUE, 
			gp = gpar(cex = cex, fontface='italic',col=textcol,lwd=1.5),
			widthOnly=FALSE);
	w <- 1.1 * convertX(attr(at,'width'),'inches',valueOnly=TRUE)
	viewportWidth <- convertX(unit(1,'npc'),'inches',valueOnly=TRUE);
	w <- w / viewportWidth
	leftName <- centerGraphic - .5 * w
	rightName <- centerGraphic + .5 * w

	if (shiftGeneNames) {
	    if (leftName < 0) {
		leftName <- 0; rightName <- w
	    }
	    if (rightName > 1) {
		rightName <- 1; leftName <- 1-w
	    }
	}

	left <- min(c(leftGraphic,leftName)) - buffer 
	right <- max(c(rightGraphic,rightName)) + buffer 

	df0uniq$start[i] <- leftName
	df0uniq$stop[i] <- rightName
	df0uniq$left[i] <- left
	df0uniq$right[i] <- right

	rowToUse <- min(which(rowUse < left))
	if ( showPartialGenes || (left >= 0 && right <= 1) ) {
	    id2row[df0uniq$idnum[i]] <- rowToUse
	    rowUse[rowToUse] <- right
	} else {
	    id2row[df0uniq$idnum[i]] <- -2   # clipping will hide this
	}
    }

    requestedRows <- rows;
    optRows <- max(c(0,which(rowUse > 0)));
    if (computeOptimalRows) { return (optRows) }

    save(df,flat,df0,df1,df2,df0uniq,id2row,file="debug.Rdata");

    rows <- min(requestedRows,optRows);

    if (is.character(args[['requiredGene']]) ) {
	requiredGeneIdx <- min(which(df0uniq$name==args[['requiredGene']]) )
	requiredGeneIdnum <- df0uniq$idnum[requiredGeneIdx]
	if (id2row[requiredGeneIdnum] > rows) {
	    for (id in which(id2row == 1)){
		if (df0uniq$left[id] < df0uniq$right[requiredGeneIdx] &&
		    df0uniq$right[id] > df0uniq$left[requiredGeneIdx] ) {
		    id2row[id] = rows+2
		}
	    }
	    id2row[requiredGeneIdnum] <- 1
	}

    }

    if (optRows > requestedRows && args[['warnMissingGenes']]) {
	omitIdx <- which(id2row > rows)
	assign("omittedGenes",as.character(df0uniq$name[omitIdx]),globalenv())
	numberOfMissingGenes <- length(omittedGenes);
	message <- paste(numberOfMissingGenes," gene",if(numberOfMissingGenes > 1) "s" else "", "\nomitted",sep="")
	pushViewport(viewport(clip='off'));
	grid.text(message ,x=unit(1,'npc') + unit(1,'lines'), y=.5, just=c('left','center'),
		  gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]));
	upViewport(1);
    }

    increment <- 1.0/rows;


    yPos <- function(id,text=FALSE) {
	if (text) {
	    return( unit((rows-id2row[id]) * increment + 4.4/7*increment, "npc") )
	} else {
	    return( unit( (rows-id2row[id]) * increment + 2/7*increment, "npc") )
	}
    }


    grid.segments(x0 = multiplier + df0$start, x1 = df0$stop, 
		  y0 = yPos(df0$idnum),
		  y1 = yPos(df0$idnum),
		  default.units = "native", 
		  gp = gpar(col = col, alpha = alpha));

    if ( "col" %in% names(df1) ) {
	col = df1$col
	fill = df1$col
    }

    grid.rect(x = multiplier + df1$start, width = df1$width, 
	      just = "left", 
	      y = yPos(df1$idnum),
	      height = unit(height * increment, "npc"), 
	      default.units = "native", 
	      gp = gpar(fill = fill, col = col, alpha = alpha));

    if ( "textcol" %in% names(df0uniq) ) {
	textcol = df0uniq$textcol
	fill = df0uniq$textcol
    }

    for (i in 1:dim(df0uniq)[1]) {
	at <- arrowText(df0uniq$name[i],
			x = unit((df0uniq$start[i] + df0uniq$stop[i])/2, 'npc'),
			y = yPos(df0uniq$idnum[i], text=TRUE),
			direction = df0uniq$strand[i],
			check.overlap = TRUE, 
			gp = gpar(cex = cex, fontface='italic',col=textcol,lwd=1.5));
	grid.draw(at);
    }
}

getGenericPlotHeight <- function (no,nrow)
{
    if (no == 0)
    {
	return (0);
    } else
    {
	return (no+nrow);
    }
}

#############################################################
#
# generic plot (input has four columns chr,start,end,score)
#
panel.generic <- function (genscore,unit,start,end,score,color=NULL,...)
{
    start=genscore$start/unit;
    end=genscore$end/unit;
    score=genscore$score;
    len=length(start);

	print('start');
print(start);
print('end');
print(end);
    if (len != length(end) || len != length(score))
    {
	warning("Generic file must have equal columns each row!");
    }

    if(length(start)*length(end)*length(score) != 0)
    {#grid.rect doesn't work when input length is zero
    plot_grob=grid.rect(x=start,y=0,width=end-start,height=score,gp=gpar(fill=color,col=color),default.units='native',just=c('left','bottom'));
    }
}
panel.piechart<-function(slices,labels,colors,title)
{
    oldpar=par(no.readonly=TRUE);
    pushViewport(viewport(
			  layout=grid.layout(1,2,widths=unit(c(1,1),c('null','null')),heights=unit(c(1,2),c('null','lines')))
			  ));
    #piechart
    pushViewport(viewport(layout.pos.row=1,layout.pos.col=1));
    par(plt=gridPLT());
    pie(slices,col=colors,labels=NA,border=NA);
    par(oldpar);
    popViewport(1);

    #title
    #pushViewport(viewport(layout.pos.row=2,layout.pos.col=1));
    #grid.text(title);
    #popViewport(1);

    #legend
    pushViewport(viewport(layout.pos.row=1,layout.pos.col=2));
    par(plt=gridPLT(),new=TRUE);
    legend('center',fill=colors,legend=labels,cex=0.5);
    par(oldpar);
    popViewport(1);

    upViewport(1);
}

readCatKey <- function (key,header=TRUE)
{
    #key file contains: key\tcolor\tdescription
    x=read.delim(key,header=header);
    return(x);
}
#############################################################
#
# category plot (input has four columns chr,start,end,annotation)
#
panel.category <- function (x,unit,key=NULL,alpha=1,...) 
{
    start=x$start;
    end=x$end;
    annotation=as.factor(x$annotation);

print('category start/end');
print(start);
print(end);
    if (length(start) != length(end) || length(start) != length(annotation))
    {
	warning("Category annotation must have equal columns each row!");
    }
    if (is.null(key))
    {
	levels(annotation)=rainbow(length(levels(annotation))); 
    } else
    {
	level2color=readCatKey(key);
	keyMatch=levels(annotation) %in% level2color$key;

	if (length(which(keyMatch)) != length(levels(annotation)) )
	{
	    warning("Not all levels found in annotation are defined by the category key file!");
	    warning("Use rainbow instead\n");
	    levels(annotation)=rainbow(length(levels(annotation))); 
	} else
	{
	    for (i in 1:length(levels(annotation)) )
	    {
		levels(annotation)[i]=as.character(level2color$color[level2color$key==levels(annotation)[i]]);
	    }
	}
    }
	print('current viewport xscale');
	vp=current.viewport();
	print(vp$xscale);
    grid.rect(  x=start/unit,
	      width=(end-start)/unit,
	      gp=gpar(fill=as.character(annotation),lty=0,alpha=alpha),
	      just=c("left","center"),
	      default.units="native",
	      )
}
######################################
#create barchart for continuous annotation and LD category
panel.myBarchart=function(count,name,args,ylab=NULL)
{
    dimCount=length(dim(count));
    colors=args[['ColorsForBarchart']][1:dimCount];

    pushViewport(viewport(layout=grid.layout(2,1,heights=unit(c(1,1),c('lines','null')))));

    pushViewport(viewport(layout.pos.row=2));
    oldpar=trellis.par.get();
    newpar=oldpar;
    newpar$superpose.polygon$col=colors;
    trellis.par.set(newpar);
    #you have to use print method in lattice, otherwise the plot is not limitted to current viewport
    print(barchart(count,stack=FALSE,auto.key=list(space='right'),xlab='Count',col=colors,border='transparent',title=paste(name,"summary"),horizontal=TRUE,ylab=ylab),newpage=FALSE);
    trellis.par.set(oldpar);
    upViewport(1);

    pushViewport(viewport(layout.pos.row=1));
    grid.text(paste(name,"category"),just=c("center"));
    upViewport(2);
}

grid.legend <- function (pch, labels, frame = TRUE, hgap = unit(0.5, "lines"), 
			 vgap = unit(0.5, "lines"), default.units = "lines", gp = gpar(), 
			 draw = TRUE, vp = NULL,args=NULL) 
{
    labels <- as.character(labels);
    nkeys <- length(labels);
    if (length(pch) != nkeys)
	stop("'pch' and 'labels' not the same length");
    if (!is.unit(hgap))
	hgap <- unit(hgap, default.units);
    if (length(hgap) != 1)
	stop("'hgap' must be single unit");
    if (!is.unit(vgap))
	vgap <- unit(vgap, default.units);
    if (length(vgap) != 1)
	stop("'vgap' must be single unit");
    legend.layout <- grid.layout(nkeys, 3, widths = unit.c(unit(2,
								"lines"), max(unit(rep(1, nkeys), "strwidth", as.list(labels))),
							   hgap), heights = unit.pmax(unit(2, "lines"), vgap + unit(rep(1,
															nkeys), "strheight", as.list(labels))));
    fg <- frameGrob(layout = legend.layout, vp = vp, gp = gp);
    for (i in 1L:nkeys) 
    {
	if (length(gp$col)>1 )
	{
	    gp.local=gp;
	    gp.local$col=gp.local$col[i];
	    fg <- placeGrob(fg, pointsGrob(0.5, 0.5, pch = pch[i],gp=gp.local), 
			    col = 1, row = i);

	    if (! is.null(args[['legendColor']]))
	    {
		gp.local$col=args[['legendColor']];
	    }
	    fg <- placeGrob(fg, textGrob(labels[i], x = 0, y = 0.5, 
					 just = c("left", "centre"),gp=gp.local), col = 2, row = i);
	} else
	{
	    fg <- placeGrob(fg, pointsGrob(0.5, 0.5, pch = pch[i]), 
			    col = 1, row = i);
	    fg <- placeGrob(fg, textGrob(labels[i], x = 0, y = 0.5, 
					 just = c("left", "centre")), col = 2, row = i);
	}
    }
    if (draw)
	grid.draw(fg);
    fg;
}

#parse or set default Y labels, arguments will be recycled if there are fewer than needed
getXYplotYlab <- function ( args ,ylab)
{
    if(args[['xyplotlog']] == 'YES')
    {
	return (bquote(paste(log[10],.(ylab),sep="")));
    } else if (args[['xyplotlog']] == 'MINUS')
    {
	return (bquote(paste(-log[10],.(ylab),sep="")));
    }  else
    {
	return (ylab);
    }
}
#expand range, if two ends equal, treat it differently
expandRange <- function (x)
{
    result = extendrange(x,f=0.1);
    if (result[1] == result[2])
    {
	if(result[1] == 0)
	{
	    result[1]=-0.5;
	    result[2]=0.5;
	} else
	{
	    result[1] = result[1] - abs(result[1]*0.5);
	    result[2] = result[2] + abs(result[2]*0.5);
	}
    }
    return(result);
}


#############################################################
#
# Assemble a plot zooming in on a region from various pieces
# including metal output (with positions added), ld (ala newfugue), recombination rate data,
# genes data (refFlat), etc.
# 
# NB: *** passing in entire args list *** 
#
#generic mark
zplot <- function(metal,ld=NULL,recrate=NULL,genscore=NULL,category_anno=NULL,refidx=NULL,nrugs=0,postlude=NULL,args=NULL,heatmapData=NULL,...)
{
    print(1200);
    print(str(metal));
    #get number of generic plots and category plots to adjust widths and heights
    genericNo=0;
    categoryNo=0;
    xyplotNo=0;

    if(!is.null(args[['xyplotCol']]))
    {
	xyplotNo = length(unlist(strsplit(args[['xyplotCol']],',')));
    }

    if (length(names(genscore)) > 0)
    {
	genericNo=length(names(genscore));
    }
    if (length(names(category_anno)) > 0)
    {
	categoryNo=length(names(category_anno));
    }

    if (! args[['showGeneric']])
    {
	genericNo=0;
    }

    if (! args[['showCategory']])
    {
	    categoryNo=0;
    }
    if (xRange[1]<0)
    {
	    xRange[1]=0;
    }


    refSnp <- metal$MarkerName[refidx];

    metal$P.value <- as.numeric(metal$P.value);

    if ( char2Rname(args[['weightCol']]) %in% names(metal) )
    {
	metal$Weight <- metal[ ,char2Rname(args[['weightCol']]) ];
	dotSizes <- rescale( log(pmax(1,metal$Weight)), c(log(1000), log(100000)), 
			    c(args[['smallDot']],args[['largeDot']] ) ) ; 
    } else {
	dotSizes <- rep(args[['largeDot']], dim(metal)[1] );
	if (! is.null(args[['refDot']]) ) 
	{
	    dotSizes[refidx] <- args[['refDot']];
	} 
    }	

    if ( is.null(args[['refDot']]) ) 
    {
	# this avoids problems downstream, but dotSize[refidx] has already been set in most cases.
	args[['refDot']] <- args[['largeDot']];
    }

    grid.newpage();
    # push viewports just to calculate optimal number of rows for refFlat
    pushViewport(viewport(
			  layout=grid.layout(2+3+4,1+2, 
					     widths=unit(c(5,1,5),c('lines','null','lines')),
					     heights=unit(c(.5,      3,nrugs,      1,     1,      1,   2*args[['rfrows']],       4,.5),
							  c('lines','lines',        'lines','lines','null','lines',              'lines', 'lines','lines'))
					     )
			  ));

    pvalVp=dataViewport(
			xRange,yRange,
			extension=c(0,.05),
			layout.pos.row=5,layout.pos.col=2,
			name="pvals",
			clip="off");

    pushViewport(
		 viewport(xscale=pvalVp$xscale,
			  layout.pos.row=7,
			  layout.pos.col=2,
			  name="refFlatOuter")
		 );

    optRows <- panel.flatbed(
			     flat=refFlat,
			     rows=NULL,
			     computeOptimalRows=TRUE,
			     showPartialGenes = args[['showPartialGenes']],
			     shiftGeneNames = args[['shiftGeneNames']],
			     cex=args[['geneFontSize']],
			     col=args[['geneColor']],
			     fill=args[['geneColor']],
			     multiplier=1/args[['unit']]
			     );

    if ( length( args[['rfrows']] < 2 ) ) {       # use value as upper bound
	args[['rfrows']] <- min(args[['rfrows']], optRows)
    } else {  # use smallest two values as lower and upper bounds
	args[['rfrows']] <- sort(args[['rfrows']])
	rows <- min( args[['rfrows']][2], optRows )
	args[['rfrows']] <- max( args[['rfrows']][1], rows )
    }

    popViewport(2);

    # OK.  Now we know how many rows to use and we can set up the layout we will actually use.
    globalVp=viewport( layout=grid.layout(
					  2+3+1+2+1+2,1+2, 
					  widths=unit(
						      c(args[['axisTextSize']]*args[['leftMarginLines']],1,args[['axisTextSize']]*args[['rightMarginLines']]),c('lines','null','lines')
						      ),
					  heights=unit(
						       c(.5,
							 3,
							 nrugs,
							 1,
							 3,
							 1+args[['categoryFontSize']]*args[['categoryRows']]*categoryNo, #category plot
							 1,#spacing
							 2*args[['geneFontSize']]*args[['rfrows']],#gene annotation
							 getGenericPlotHeight((xyplotNo+genericNo),2.5*(args[['xyplotRows']]+args[['genericRows']])),#XY plot and generic plot
							 4,
							 1),

						       c('lines',
							 'lines',
							 'lines',
							 'lines',
							 'null',
							 'lines',
							 'lines',
							 'lines', 
							 'lines',
							 'lines',
							 'lines')
						       )
					  ) );
    pushViewport(globalVp);

    ##
    # layout (top to bottom with generic plot and category plot)
    # ----------------------
    #    spacer
    #    title text
    #    rugs
    #    separation
    #    pvals
    #    separation,category strip1,category strip2,...
    #    separation
    #    genes
    #	 separation1,xyplot1,separation2,xyplot2,...  || separation1,generic plot1,separation2,generic plot2,...
    #    subtitle text 
    #    spacer
    #
    # layout (left to right)
    # ----------------------
    #    vertical axes and labeling
    #    main data panels, titles, horizontal axes, etc.
    #    vertical axes and labeling
    #

    ########## title text
    titleVp=viewport(
		     layout.pos.row=2,layout.pos.col=2,
		     name="title",
		     clip="off");
    pushViewport(titleVp);
    grid.text(args[['title']],gp=gpar(cex=2,col=args[['titleColor']]));
    upViewport(1);

    ########## rugs for snpsets
    pushViewport(viewport(xscale=pvalVp$xscale,layout.pos.row=3,
			  layout.pos.col=2,name="rugs",clip="off"));
    i <- nrugs;
    for (snpset in levels(rug$snp_set)) {
	grid.text(as.character(snpset),x=unit(-.25,"lines"),
		  y=(i-.5)/nrugs, just="right",
		  gp=gpar(col=args[['rugColor']], alpha=args[['rugAlpha']],cex=.90*args[['axisTextSize']])
		  );
	i <- i-1;
    }

    pushViewport(viewport(xscale=pvalVp$xscale,layout.pos.row=3,
			  layout.pos.col=2,name="rugsClipped",clip="on"));
    i <- nrugs;
    for (snpset in levels(rug$snp_set)) {
	panel.rug( rug[ which(rug$snp_set==snpset), "pos" ] , 
		  start = (i-1)/(nrugs) + (.15/nrugs),
		  end = (i)/(nrugs) - (.15/nrugs),
		  y.units=rep("native",2),
		  col=args[['rugColor']],
		  alpha=args[['rugAlpha']]
		  );
	i <- i-1;
    }

    upViewport(2);
    ########## pvals
    # this viewport is defined above
    #            pvalVp=dataViewport(
    #			    xRange,yRange,
    #                extension=c(0,.05),
    #                layout.pos.row=5,layout.pos.col=2,
    #			    name="pvals",
    #                clip="off");
    pushViewport(pvalVp);
    grid.yaxis(at=args[['yat']],gp=gpar(cex=args[['axisSize']],col=args[['frameColor']],alpha=args[['frameAlpha']]));
    #		grid.xaxis(at=args[['xat']],gp=gpar(cex=args[['axisSize']],col=args[['frameColor']],alpha=args[['frameAlpha']]));
    if (length(args[['ylab']])>1) {
	grid.text(x=unit(args[['ylabPos']],'lines'),label=args[['ylab']],rot=90, gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]) );
    } else {
	grid.text(x=unit(args[['ylabPos']],'lines'),label=expression(paste(-log[10] ," P")), rot=90,   gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]) );
    }

    pushViewport(dataViewport(extension=c(0,.05),xRange,recrateRange,name='recrate',clip="off"));
    if ( args[['showRecomb']] ) {
	grid.yaxis(main=F,gp=gpar(cex=args[['axisSize']],col=args[['recombAxisColor']],alpha=args[['recombAxisAlpha']]));
	grid.text(x=unit(1,'npc')+unit(args[['recombPos']],'lines'),
		  label="Recombination rate (cM/Mb)",rot=270,
		  gp=gpar(cex=args[['axisTextSize']],col=args[['recombAxisColor']],alpha=args[['recombAxisAlpha']]));
    }


    if ( args[['showRecomb']] && !args[['recombOver']]) {
	pushViewport(dataViewport(extension=c(0,.05),xRange,recrateRange,name='recrateClipped',
				  clip="on"));
	if (args[['recombFill']]) {
	    grid.polygon(x=recrate$pos,y=recrate$recomb,
			 gp=gpar(alpha=args[['recombFillAlpha']],col=args[['recombColor']],fill=args[['recombColor']]),
			 default.units='native'
			 );
	} else {
	    panel.xyplot(recrate$pos,recrate$recomb,type='l',lwd=2,alpha=args[['recombLineAlpha']],col=args[['recombColor']]);
	}
	upViewport(1)  
    }

    pushViewport(viewport(clip="on",xscale=pvalVp$xscale,yscale=pvalVp$yscale,name='pvalsClipped'));
    grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
    if (! is.null(refidx)) {
	if (!is.null(args[['refsnpName']])) {
	    grid.refsnp(name=args[['refsnpName']],pos=metal$pos[refidx]);
	} else{
	    grid.refsnp(name=refSnp,pos=metal$pos[refidx]);
	}
    }
    groupIds <-  sort(unique(metal$group))
    print(table(metal$group));

    if (args[['bigDiamond']] && args[['showRefsnpAnnot']]) {
	grid.points(x=metal$pos[refidx],y=transformation(metal$P.value[refidx]), 
		    gp=gpar(col=args[['refsnpColor']],fill=args[['refsnpColor']],cex=1.6*args[['refDot']],alpha=.2),
		    pch=23,
		    default.units='native'
		    );
    }

    for (i in groupIds) 
    { 
	idx <- which(metal$group == i);
	gmetal <- metal[idx,]
	colors <- args[['ldColors']][gmetal$group]; 
	colors[which(gmetal$pch %in% 21:25)] <- 'gray20';
	grid.points(x=gmetal$pos,y=transformation(gmetal$P.value),
		    pch=gmetal$pch,
		    gp=gpar(
			    cex=dotSizes[idx], 
			    col=colors,
			    fill=args[['ldColors']][gmetal$group]
			    )); 
    }


    if ( args[['showRecomb']] && args[['recombOver']]) {
	pushViewport(dataViewport(extension=c(0,.05),xRange,recrateRange,name='recrateClipped',
				  clip="on"));
	if (args[['recombFill']]) {
	    grid.polygon(x=recrate$pos,y=recrate$recomb,
			 gp=gpar(alpha=args[['recombFillAlpha']],col=args[['recombColor']],fill=args[['recombColor']]),
			 default.units='native'
			 );
	} else {
	    panel.xyplot(recrate$pos,recrate$recomb,type='l',lwd=2,alpha=args[['recombLineAlpha']],col=args[['recombColor']]);
	}
	upViewport(1); 
    }
    grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));

    pushViewport(viewport(clip="on",name='legend'));

    breaks <- union(args[['ldCuts']],c(0,1));
    breaks <- sort(unique(breaks));
    nb <- length(breaks);
    cols <- args[['ldColors']]
    cols <- rep(cols, length=nb+2);
    rl <- ribbonLegend(
		       breaks=breaks,
		       cols=cols[2:(1+nb)],
		       gp=gpar(cex=args[['legendSize']],col=args[['frameColor']],alpha=args[['frameAlapha']])
		       );

    if (args[['legend']] == 'auto') { 
	args[['legend']] = AutoLegendSide(transformation(metal$P.value),metal$pos,xRange); 
    }

    if (tolower(args[['legend']]) %in% c('left','right')) {
	pushViewport(viewport(name='legendVp',
			      x=if (args[['legend']] == 'left') unit(2.5,"char") else unit(1,'npc') - unit(2.5,'char'),
			      y=unit(1,'npc') - unit(.5,'char'),
			      just=c('center','top'),
			      width=unit(4,'char'),
			      height=unit(8,'lines')
			      ));
	grid.rect(gp=gpar(col='transparent',fill='white',alpha=args[['legendAlpha']]));
	grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));

	pushViewport(viewport(name='ribbonLegend',
			      y=0,
			      just=c('center','bottom'),
			      width=unit(4,'char'),
			      height=unit(7,'lines')
			      ))
	grid.draw(rl);
	upViewport(1);

	pushViewport(viewport(name='LDTitle',
			      clip="off", 
			      #x=unit(2.5,"char"),
			      width=unit(4,"char"),
			      y=unit(1,'npc') - unit(.25,'char'),
			      just=c('center','top'),
			      height=unit(1,'lines')
			      ))
	grid.text(args[['LDTitle']], gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
	upViewport(1);

	upViewport(1);
    } # end if show legend on left or right

    upViewport(4);   
    ########## category plot
    if ( categoryNo && args[['showCategory']] ) 
    {
	pushViewport(
		     viewport(
			      layout.pos.row=6,
			      layout.pos.col=2,
			      name="categoryOuter")
		     );
	pushViewport(
		     viewport(
			      name="categoryInner",
			      clip="on",
			      layout=grid.layout(2,1,
						 heights=unit(c(1,categoryNo),c("null","null")) 
						 )
			      ) );

	pushViewport(
		     viewport(
			      name="categorySpacer",
			      layout.pos.row=1,
			      layout.pos.col=1
			      )
		     );
	upViewport(1);

	pushViewport(viewport(
			      name="categoryPlotArea",
			      clip="on",
			      layout=grid.layout(categoryNo,1),
			      layout.pos.row=2,
			      layout.pos.col=1
			      ));

	for ( i in 1:categoryNo)
	{
	    pushViewport(
			 viewport(
				  xscale=pvalVp$xscale,
				  layout.pos.row=i,
				  layout.pos.col=1)
			 );

	    panel.category(category_anno[[i]],args[['unit']],key=args[['categoryKey']],alpha=args[['categoryAlpha']]);
print(names(category_anno)[i]);
	    grid.text(
		      label=names(category_anno)[i],
		      just=c("center"),
		      gp=gpar(col=args[['categoryFontColor']],cex=args[['categoryFontSize']],alpha=args[['categoryAlpha']])
		      );
	    upViewport(1);
	}
	grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
	upViewport(1);

	upViewport(2);
    }
    ########## annotation (genes)
    if(args[['rfrows']] > 0) 
    {
	pushViewport(
		     viewport(xscale=pvalVp$xscale,
			      layout.pos.row=8,
			      layout.pos.col=2,
			      name="refFlatOuter")
		     );
	pushViewport(
		     viewport(xscale=pvalVp$xscale,
			      name="refFlatInner",
			      clip="on")
		     );
	panel.flatbed(
		      flat=refFlat,
		      showPartialGenes = args[['showPartialGenes']],
		      shiftGeneNames = args[['shiftGeneNames']],
		      rows=args[['rfrows']], 
		      cex=args[['geneFontSize']],
		      col=args[['geneColor']],
		      fill=args[['geneColor']],
		      multiplier=1/args[['unit']]);
	upViewport(1);

	#grid.rect(gp=gpar(col='white'));
	grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));

	panel.hilite(
		     range=c(args[['hiStartBP']]/args[['unit']],args[['hiEndBP']]/args[['unit']]),
		     fill=args[['hiColor']],
		     alpha=args[['hiAlpha']]
		     );
	upViewport(1);
    }
    #create an area for both xyplot and generic plot
    #the purpose of this is to distribute the plotting area proportionately, based on number of plots we'll draw
    pushViewport(
		 viewport(
			  layout.pos.row=9,
			  layout.pos.col=2,
			  name="XYplotANDGenericOverall",
			  clip="off",
			  layout=grid.layout(2,1,heights=unit(c(xyplotNo,genericNo),"null")) )
		 );
    #XYplot
    if ( xyplotNo )
    {
	pushViewport(
		     viewport(
			      layout.pos.row=1,
			      name="XYplotOuter",
			      clip="off")
		     );
	pushViewport(
		     viewport(
			      name="XYplotInner",
			      layout=grid.layout(xyplotNo,1),
			      )
		     );
	#every XY plot will get its own label
	#the title of every plot will be same as the column name from which the data points come
	xyplotcol = unlist(strsplit(args[['xyplotCol']],','));
	#y-axis label will be recycled
	xyplotylab = rep(unlist(strsplit(args[['xyplotylab']],',')),xyplotNo)[1:xyplotNo];

	for (xyplot_index in 1 : xyplotNo)
	{
	    #individual xyplot
	    xyplotylab_local = getXYplotYlab(args,xyplotylab[xyplot_index]);
	    if (length(which(is.na(metal[,xyplotcol[xyplot_index]]))) != length(metal[,xyplotcol[xyplot_index]]) &&
	        length(metal[,xyplotcol[xyplot_index]]) != 0)
	    {
		xyplotDataRange=expandRange(range(metal[,xyplotcol[xyplot_index]],na.rm=TRUE));
	    } else
	    {
		#when is no meaningful data, use this as default scale
		xyplotDataRange=c(0,1);
	    }

	    pushViewport(viewport(layout.pos.row=xyplot_index,layout.pos.col=1));
	    #draw a y lab for each plot
	    grid.text( x=unit(args[['ylabPos']],'lines'), label=xyplotylab_local,rot=90, gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]));

	    pushViewport(viewport(
				  layout=grid.layout(2,1,
						     heights=unit(c(1,5/xyplotNo*args[['xyplotRows']]),c("lines","null"))
						     )
				  ));

	    #plot title
	    print(1651);
	    pushViewport(
			 viewport(layout.pos.row=1,layout.pos.col=1,name=paste("xyplotTitle",xyplot_index,sep=""))
			 );
	    grid.text( xyplotcol[xyplot_index] );
	    upViewport(1);

	    #plot XY plot
	    #data has been converted to numerical
	    print(1659);
	    pushViewport(#a simpler way to adjust scale is to use extension
			 viewport(xscale=pvalVp$xscale,yscale=xyplotDataRange,
				  layout.pos.row=2,
				  layout.pos.col=1,
				  name=paste("xyplotPlotArea",xyplot_index,sep=""),
				  clip="off",
				  ));
	    print(1668);
	    grid.yaxis(at=args[['yat']],
		       gp=gpar(cex=args[['axisSize']]*0.8,col=args[['frameColor']],alpha=args[['frameAlpha']] )
		       );


	    print(1671);
	    pushViewport(
			 viewport(xscale=xRange,yscale=xyplotDataRange,name=paste('xyplot',xyplot_index,sep=""),clip="on")
			 );
	    print(1677);
	    print(metal$pos);
	    print(metal[,xyplotcol[xyplot_index]]);
	    grid.points(x=metal$pos,y=metal[,xyplotcol[xyplot_index]],gp=gpar(col=args[['xyplotColor']]));
	    print(1699);
	    upViewport(1);
	    grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
	    print(1702);

	    upViewport(1);
	    upViewport(2);
	}
	upViewport(2);
    }
    ###########	multiple generic plots
    if ( genericNo && args[['showGeneric']] ) 
    {
	pushViewport(
		     viewport(
			      layout.pos.row=2,
			      name="genericOuter",
			      clip="off")
		     );
	pushViewport(
		     viewport(
			      name="genericInner",
			      layout=grid.layout(genericNo,1),
			      )
		     );
	if (length(args[['genericylab']]) > 0) 
	{
	    grid.text(x=unit(args[['ylabPos']],'lines'),label=args[['genericylab']], rot=90,gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]));
	} else
	{
	    grid.text( x=unit(args[['ylabPos']],'lines'), label="Normalized Score",rot=90, gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']]));
	}


	for (genscore_index in 1:length(names(genscore)) )
	{
	    ##########generic plot title
	    if (length(which(is.na(genscore[[genscore_index]]$score))) != length(genscore[[genscore_index]]$score) &&
	    	length(genscore[[genscore_index]]$score) != 0 )
	    {
		genscoreRange=expandRange(range(genscore[[genscore_index]]$score,na.rm=TRUE));
	    } else
	    {
#when is no meaningful data, use this as default scale
		genscoreRange=c(0,100); 
	    }

	    pushViewport(viewport(xscale=pvalVp$xscale,layout.pos.row=genscore_index,layout.pos.col=1));

	    pushViewport(viewport(xscale=pvalVp$xscale,
				  layout=grid.layout(2,1,
						     heights=unit(c(1,5/genericNo*args[['genericRows']]),c("lines","null"))
						     )
				  ));

	    pushViewport(
			 viewport(layout.pos.row=1,layout.pos.col=1,name=paste("genericTitle",genscore_index,sep=""))
			 );
	    grid.text( names(genscore[genscore_index]) );
	    upViewport(1);
	    ##########generic plot
	    pushViewport(
			 viewport(xscale=pvalVp$xscale,yscale=genscoreRange,
				  layout.pos.row=2,
				  layout.pos.col=1,
				  name=paste("genericPlot",genscore_index,sep=""),
				  clip="off",
				  ));
	    #    pushViewport(
	    #	    dataViewport(extension=c(0,.05),xRange,genscoreRange,name=paste('genscore',genscore_index,sep=""),clip="off",
	    #	    ));
	    grid.yaxis(at=args[['yat']],
		       gp=gpar(cex=args[['axisSize']]*0.8,col=args[['frameColor']],alpha=args[['frameAlpha']] )
		       );


	    #upViewport(1);

	    pushViewport(
			 viewport(xscale=xRange,yscale=genscoreRange,name=paste('genscore',genscore_index,sep=""),clip="on")
			 );
            
print('pvalxscale');
print(pvalVp$xscale);
print('xrange');
print(xRange);
	print('generic name');
print(names(genscore[genscore_index]));
	    panel.generic(
			  genscore[[genscore_index]],unit=args[['unit']],color=args[['genericColor']]);
	    upViewport(1);
	    grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));

	    upViewport(1);
	    upViewport(2);
	}
	upViewport(2);
    }
    upViewport(1); #get out of xyplot and generic plot region
    #add xaxis 
    pushViewport(
		 viewport(xscale=pvalVp$xscale,
			  layout.pos.row=9,
			  layout.pos.col=2,
			  name="xaxis",
			  )
		 );

    if ( !is.null(args[['xnsmall']]) && !is.null(args[['xat']]) )
    {
	grid.xaxis(
		   at=args[['xat']], label=format(args[['xat']], main=FALSE,nsmall=args[['xnsmall']]),gp=gpar(cex=args[['axisSize']],col=args[['frameColor']],alpha=args[['frameAlpha']])
		   );
    } else if (!is.null(args[['xat']]))
    {
	grid.xaxis(
		   at=args[['xat']],gp=gpar(cex=args[['axisSize']],main=FALSE,col=args[['frameColor']],alpha=args[['frameAlpha']])
		   );
    } else
    {
	local.xmin=pvalVp$xscale[1];
	local.xmax=pvalVp$xscale[2];
	local.range=local.xmax-local.xmin;
	local.digit=floor(-log10(local.range)+2);
	local.xmin=round(local.xmin+local.range*0.1,local.digit);
	local.xmax=round(local.xmax-local.range*0.1,local.digit);
	local.xat=seq(local.xmin,local.xmax,length.out=5);
	grid.xaxis(
		   at=local.xat,gp=gpar(cex=args[['axisSize']],main=FALSE,col=args[['frameColor']],alpha=args[['frameAlpha']])
		   );
    }

    grid.text(
	      paste('Position on',chr2chrom(args[['chr']]),unit2char(args[['unit']])), y=unit(args[['xlabPos']],'lines'),just=c('center',"bottom"),	gp=gpar(cex=args[['axisTextSize']], col=args[['axisTextColor']], alpha=args[['frameAlpha']])
	      );
    upViewport(1);
    if (is.character(postlude) && file.exists(postlude)) {
	source(postlude);
    }
    #end of first page
    ############################################################################
    #SECOND PAGE (INTERACTION HEATMAP) BEGINS HERE
    ############################################################################
    if(!is.null(args[['heatmapFile']]))
    {
	grid.newpage();
	pushViewport(viewport());

	#use levelplot in lattice package to draw heatmap
	heatmapObj <- levelplot(value~chr1*chr2,heatmapData,
		  colorkey=list(tick.number=10),
		  scales=list(tick.number=5),
		  xlim=pvalVp$xscale,
		  col.regions=colorRampPalette(unlist(strsplit(args[['heatmapColor']],',')))(100),
		  xlab=paste("chr",args[['chr']],unit2char(args[['unit']])),
		  ylab=paste("chr",args[['chr2']],unit2char(args[['unit']])),
		  main=paste("chr",args[['chr']],"chr",args[['chr2']],"interaction\n",args[['heatmapTitlePlus']])
		  );
	print(heatmapObj,newpage=FALSE,more=TRUE);
	upViewport(1);
    }
}  ## end zplot

grid.log <- function(args,metal,linespacing=1.5,debug=FALSE)
{
    labels=c("date");
    values=c(date());
    labels=c(labels,"build");
    values=c(values,args[['build']]);
    labels=c(labels,"display range");
    values=c(values,paste( 'chr',args[['chr']],":",args[['start']], "-", args[['end']],sep=""));
    if (args[['hiStart']] && args[['hiEnd']] && args[['hiStartBP']] && args[['hiEndBP']])
    {
	labels=c(labels,"hilite range");
	values=c(values,paste( args[['hiStart']], "-", args[['hiEnd']], " [",args[['hiStartBP']],"-",args[['hiEndBP']], "]"));
    }
    labels=c(labels,"reference SNP");
    values=c(values,args[['refsnp']]);

    if (!is.null(args[['reload']])) {
	labels=c(labels,"reload");
	values=c(values,args[['reload']]);
    }

    if(! is.null(args[['reload']]) || debug){
	labels=c(labels,"data reloaded from");
	values=c(values,args[['rdata']]);
    }

    labels=c(labels,"number of SNPs plotted");
    values=c(values,as.character(dim(metal)[1]));

    labels=c(labels,paste("max",args[['pvalCol']]));
    maxIdx <- which.max(transformation(metal$P.value));
    maxName <- as.character(metal$MarkerName[maxIdx]);
    maxNegLogP <- transformation(metal$P.value[maxIdx]);
    maxPSci <- log2sci(-maxNegLogP)
    values=c(values,paste(maxPSci," [", maxName ,"]",sep=""));

    labels=c(labels,paste("min",args[['pvalCol']]));
    minIdx <- which.min(transformation(metal$P.value));
    minName <- as.character(metal$MarkerName[minIdx]);
    minNegLogP <- transformation(metal$P.value[minIdx]);
    minPSci <- log2sci(-minNegLogP)
    values=c(values,paste(minPSci," [", minName ,"]",sep=""));

    if (length(which(metal$annot!='none'))>0)
    {
	labels=c(labels,paste(args[['annotName']]," summary",sep=''));
	annotSummary=table(metal$annot);
	local.value='';
	for (i in 1:length(annotSummary))
	{
	    local.label=paste("'",names(annotSummary)[i],"'",sep='');
	    local.value=paste(local.value,annotSummary[[i]],local.label,sep=' ');
	}
	values=c(values,local.value);
    }

    if (TRUE) { 
	oG <- omittedGenes;
	while (length(oG) > 0) {
	    labels=c(labels,"omitted Genes");
	    values=c(values,paste(oG[1:min(length(oG),3)],collapse=", "));
	    oG <- oG[-(1:3)]
	}
    }
    if (TRUE) { 
	w <- warningMessages;
	while (length(w) > 0) {
	    labels=c(labels,"Warning");
	    values=c(values,w[1]);
	    w <- w[-1]
	}
    }

    labels=paste(labels, ":  ",sep='');

    #print out
    grid.text(labels,x=.3,y=unit(1,'npc') - unit(linespacing *(1:length(labels)),'lines'), just='right',gp=gpar(cex=0.7));
    grid.text(values,x=.3,y=unit(1,'npc') - unit(linespacing *(1:length(values)),'lines'), just='left',gp=gpar(cex=0.7));

    if (! is.null(args[['categoryKey']]))
    {
	grid.text("Category Plot Legend",x=0.5,hjust='center',y=unit(1,'npc')-unit(linespacing*(length(labels)+1),'lines'),vjust='top',gp=gpar(col=args[['legendColor']]));

	key=args[['categoryKey']];
	info=readCatKey(key);
	nrow=dim(info)[1];
	legend.gb <- grid.legend(
				 rep(15,nrow),
				 as.character(info$description),
				 draw=FALSE,
				 gp=gpar(col=as.character(info$color)),
				 args=args,
				 );
	legend.vp <- viewport (x=0.2,
			       y=unit(1,'npc') - unit(linespacing*(length(labels)+2),'lines'),
			       just=c('left','top'),
			       width=1.1*grobWidth(legend.gb),
			       height=1.1*grobHeight(legend.gb),
			       );
	pushViewport(legend.vp);
	grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
	grid.draw(legend.gb);
	upViewport(1);
    }

    if ( 'annot' %in% names(metal) && args[['showAnnot']] ) {
	annotlabels <- levels(as.factor(metal$annot))
	pch <- rep(args[['annotPch']],length=length(annotlabels));
	key <- simpleKey(text=annotlabels);
	key$points$pch=pch;
	key$points$col="navy";
	key$points$fill="lightskyblue";
	keyGrob <- draw.key(key,draw=FALSE);
	annotationBoxTop <- unit(0.95,'npc');
	annotationBoxHeight <- unit(3,"lines") + grobHeight(keyGrob);
	pushViewport(viewport(x=.90,y=annotationBoxTop,width=grobWidth(keyGrob),
			      height=annotationBoxHeight,just=c('right','top')));
	pushViewport(viewport(y=unit(.75,'lines'),height = grobHeight(keyGrob),just=c('center','bottom')));
	draw.key(key,draw=TRUE);
	grid.rect();
	popViewport();
	grid.text(args[['annotName']],x=.5,y=unit(1,'npc') - unit(1,'lines'),just=c('center','top'))
	popViewport();
	} else { if (args[['showAnnot']]) { 
	    annotlabels <- c('no annotation','framestop','splice','nonsyn','coding','utr','tfbscons','mcs44placental');
	    pch <- args[['annotPch']];
	    annotlabels <- c(annotlabels[-1],annotlabels[1])
	    pch <- c(pch[-1],pch[1])
	    key <- simpleKey(text=annotlabels);
	    key$points$pch=pch;
	    key$points$col="navy";
	    key$points$fill="lightskyblue";
	    keyGrob <- draw.key(key,draw=FALSE);
	    annotationBoxTop <- unit(0.95,'npc');
	    annotationBoxHeight <- unit(3,"lines") + grobHeight(keyGrob);
	    pushViewport(viewport(x=.90,y=annotationBoxTop,width=grobWidth(keyGrob),
				  height=annotationBoxHeight,just=c('right','top')));
	    popViewport();
    } }

    breaks <- union(args[['ldCuts']],c(0,1));
    breaks <- sort(unique(breaks));
    nb <- length(breaks);
    cols <- args[['ldColors']]
    cols <- rep(cols, length=nb+2);
    rl <- ribbonLegend(
		       breaks=breaks,
		       cols=cols[2:(1+nb)],
		       gp=gpar(cex=args[['legendSize']],col=args[['frameColor']],alpha=args[['frameAlapha']])
		       );

    if ( args[['legend']] %in% c('left','right') ) {
	annotlabels <- c('no annotation','framestop','splice','nonsyn','coding','utr','tfbscons','mcs44placental');
	pch <- args[['annotPch']];
	annotlabels <- c(annotlabels[-1],annotlabels[1])
	pch <- c(pch[-1],pch[1])
	key <- simpleKey(text=annotlabels);
	key$points$pch=pch;
	key$points$col="navy";
	key$points$fill="lightskyblue";
	keyGrob <- draw.key(key,draw=FALSE);
	annotationBoxTop <- unit(0.95,'npc');
	annotationBoxHeight <- unit(3,"lines") + grobHeight(keyGrob);
	pushViewport(viewport(name='legendVpPage2',
			      x=unit(.9,'npc'),
			      y=annotationBoxTop - annotationBoxHeight - unit(2,'lines'),
			      just=c('right','top'),
			      width=unit(4,'char'),
			      height=unit(8,'lines')
			      ));
	grid.rect(gp=gpar(col='transparent',fill='white',alpha=args[['legendAlpha']]));
	grid.rect(gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));

	pushViewport(viewport(name='ribbonLegendPage2',
			      y=0,
			      just=c('center','bottom'),
			      width=unit(4,'char'),
			      height=unit(7,'lines')
			      ))
	grid.draw(rl);
	upViewport(1);

	pushViewport(viewport(name='LDTitlePage2',
			      clip="off", 
			      width=unit(4,"char"),
			      y=unit(1,'npc') - unit(.25,'char'),
			      just=c('center','top'),
			      height=unit(1,'lines')
			      ))
	grid.text(args[['LDTitle']], gp=gpar(col=args[['frameColor']],alpha=args[['frameAlpha']]));
	upViewport(1);

	upViewport(1);
    }

    grid.text('Make more plots at http://enlight.usc.edu', y=unit(1,'lines'), just=c('center','bottom'));
}
#draw summary pie chart, bar chart
grid.summary=function(args,metal,genscore,category_anno)
{
    #divide plot region
    genericNames=getAnnoForPlot(args,metal,genscore);
    categoryNames=getAnnoForPlot(args,metal,category_anno);
    genericNo=length(genericNames);
    categoryNo=length(categoryNames);

    if (! args[['showCategory']])
    {
	categoryNo=0;
	categoryNames=NA;
    }
    if (! args[['showGeneric']])
    {
	genericNo=0;
	genericNames=NA;
    }
    ldRemain=1; #this is fixed, just for LD categorization plot
    genericRemain=genericNo;
    categoryRemain=categoryNo;
    maxPlotPerPage=3;
    #layout
    #######################################################
    #			LD categorization 		  #
    #			enhancer-promoter chart  	  #
    #######################################################
    #bar chart overlap with ENCODE datatracks1		  #
    #bar chart overlap with ENCODE datatracks2		  #
    #######################################################
    #at most 3 plots each page
    while(ldRemain+genericRemain+categoryRemain>0)
    {
	grid.newpage();
	if (ldRemain+genericRemain+categoryRemain>maxPlotPerPage)
	{
	    totalPlotCurrentPage=maxPlotPerPage;
	} else
	{
	    totalPlotCurrentPage=ldRemain+genericRemain+categoryRemain;
	}
	globalVp=viewport( layout=grid.layout(
					      2+totalPlotCurrentPage,3, 
					      widths=unit(
							  c(args[['axisTextSize']]*args[['leftMarginLines']],1,args[['axisTextSize']]*args[['rightMarginLines']]),c('lines','null','lines')
							  ),
					      heights=unit(
							   c(0.25, rep(1,totalPlotCurrentPage), 0.25),
							   c('lines',rep('null',totalPlotCurrentPage),'lines') )
					      ) );
	pushViewport(globalVp);

	currentPlotIdx=1;
	if (ldRemain>0 & currentPlotIdx<=maxPlotPerPage)
	{
	    #divide pichart plot region
	    pushViewport(viewport(layout.pos.row=1+currentPlotIdx,layout.pos.col=2,layout=grid.layout(3,1,heights=unit(c(0.25,1,0.25),c('lines','null','lines')))));

	    #LD categorization
	    pushViewport(viewport(layout.pos.row=2,clip='on'));
	    ld_slice=genLD_Slice(args,metal);
	    ld_slice=table(ld_slice,useNA='no');
	    panel.myBarchart(ld_slice,name='LD',args);
	    upViewport(2);
	    ldRemain=ldRemain-1;
	    currentPlotIdx=currentPlotIdx+1;
	}
	#draw barchart for category annotation
	while (currentPlotIdx<=maxPlotPerPage & categoryRemain>0)
	{
	    pushViewport(viewport(
				  layout.pos.row=1+currentPlotIdx,
				  layout=grid.layout(3,1,heights=unit(c(0.25,1,0.25),c('lines','null','lines')))
				  ));
	    pushViewport(viewport(layout.pos.row=2,clip='on'));
	    name=categoryNames[1];
	    print(2114);
	    print(metal);
	    cat_slice=as.factor(metal[[name]]);
	    levels(cat_slice)=c(levels(cat_slice),'NA');
	    cat_slice[is.na(cat_slice)]='NA';
	    lvlCount=length(levels(cat_slice));
	    cat_slice=factor(cat_slice,levels(cat_slice)[c(lvlCount,1:(lvlCount-1))]);
	    cat_slice=table(cat_slice,useNA='no');
	    panel.myBarchart(cat_slice,name,args);
	    upViewport(2);

	    if (length(categoryNames)>1) categoryNames=categoryNames[2:length(categoryNames)];
	    categoryRemain=categoryRemain-1;
	    currentPlotIdx=currentPlotIdx+1;
	}

	#generic overlapping barchart
	while(currentPlotIdx<=maxPlotPerPage & genericRemain>0)
	{
	    pushViewport(viewport(layout.pos.row=1+currentPlotIdx,layout.pos.col=2,layout=grid.layout(3,1,heights=unit(c(0.25,1,0.25),c('lines','null','lines')))
				  ));
	    pushViewport(viewport(layout.pos.row=2,clip='on'));
	    #plot with barchart function from lattice package
	    name=genericNames[1];
	    ldgroup=genLD_Slice(args,metal);

	    annotation=metal[[name]];
	    #pay attention to the order of the following two assignments
	    annotation[!is.na(annotation)]='Has annotation';
	    annotation[is.na(annotation)]='No annotation';
	    annotation=factor(annotation,levels=c('No annotation','Has annotation'));

	    count=table(ldgroup,annotation,useNA='no');
	    panel.myBarchart(count,name,args,ylab='LD interval');

	    upViewport(2);
	    if (length(genericNames)>1) genericNames=genericNames[2:length(genericNames)];
	    genericRemain=genericRemain-1;
	    currentPlotIdx=currentPlotIdx+1;
	}
	upViewport(1);
    }
}

#convert LD into count data, including count for 'no LD' variants
genLD_Slice=function(args,metal)
{
    new_slice=NA;
    new_slice=cut(metal$LD,args[['ldCutsForBarchart']],include.lowest=TRUE);
    levels(new_slice)=c(levels(new_slice),'no LD');
    lvlCount=length(levels(new_slice));

    new_slice[is.na(new_slice)]='no LD';
    #put 'no LD' in front of smallest LD interval
    new_slice=factor(new_slice,levels(new_slice)[c(lvlCount,1:(lvlCount-1))]);
		     return(new_slice);
}

#############################################################
#
# process argument list, splitting the key=value pairs
#
argv <- function(){
    args <- commandArgs(TRUE);
    newl <- list()

    for ( i in 1:length(args) ) {
	keyval <- strsplit(args[[i]],"=")[[1]];
	key <- keyval[1]; val <- keyval[2];
	newl[[ key ]] <- val; 
    }
    return(newl)
}
####################################
#get names for annotation tracks that can be used towards summary plot
getAnnoForPlot=function(args,metal,anno)
{
    annoNames=NA;
    if (length(names(anno)) > 0)
    {
	annoNames=names(anno);
	annoNames=annoNames[annoNames %in% names(metal)];
    }
    return(annoNames);
}

#################################################################################
#                                                                               #
#                         MAIN PROGRAM BEGINS HERE                              #
#                                                                               #
#################################################################################


flags <- list(flank=FALSE,reloaded=FALSE);
createdFiles <- list();
refSnpPos <- empty.data.frame();

#
# set program defaults -- may be overridden with command line arguments
#
default.args <- list(
		     genericylab= NULL,                      # overrides default label for y-axis in generic plot
		     genericRows = '3',                    # number of rows for generic plot
		     showGeneric = TRUE,	              # show generic plot?
		     generic=NULL,			      # generic table name
		     genericColor='blue',                  # color for generic score on plot

		     showCategory = TRUE,		      #show category plot?
		     category=NULL,			      #category table name (comma-delimited list)
		     categoryKey=NULL,		      #legend file for category plot (every line:key\tcolor\tdescription,1st line must be header,key is one of the categories)
		     categoryRows=1,			      #number of rows for each category plot
		     categoryFontSize=.8, 		      #font size for category plot
		     categoryFontColor='gray50',	      #font color for category plot
		     categoryAlpha=.8,		      #alpha value for category plot and text

		     xyplotCol=NULL,			   # list of column names (comma-delimited) in input for xyplot
		     xyplotRows='3',			   # number of rows for xyplot
		     xyplotColor='blue',		   # color for xyplot
		     xyplotylab=NULL,			   # comma-delimited list of labels for y-axis
		     xyplotlog = "MINUS",		   # whether to plot in log-scale (YES), -log scale (MINUS), or no log (NO)
		     
		     heatmapFile=NULL,			   #file containing matrix for heatmap plotting
		     					   #path must be ABSOLUTE!!!!!
		     heatmapColor='blue,white,red',	   #low range to high range color
		     heatmapTitlePlus=NULL,		   #additional title text

		     theme = NULL,                         # select a theme (collection of settings) for plot
		     experimental = FALSE,                 # try some experimental features?
		     format = "pdf",        	              # file format (pdf only)
		     recombTable = "results.recomb_rate",  # Recomb Rate Table (for SQL)
		     clean=TRUE,                           # remove temp files?
		     build = "hg18",                       # build to use for position information
		     metal = "metal.tbl",                  # metal output file
		     alreadyTransformed=FALSE,             # are metal p-values already -log10() -transformed?
		     pvalCol="P.value",                    # name for p-value column in metal file
		     posCol="pos",                         # name for positions column in metal file
		     markerCol="MarkerName",               # name for MarkerName column in metal file
		     weightCol="Weight",                   # name for weights column in metal file
		     ymin=0,                               # min for p-value range (expanded to fit all p-vals if needed)
		     ymax=100,                              # max for p-value range (expanded to fit all p-vals if needed)
		     yat=NULL,                             # values for y-axis ticks
		     xat=NULL,                             # values for x-axis ticks
		     xnsmall=NULL,                         # number of digits after decimal point on x-axis labels
		     chr = NULL,                           # chromosome
		     chr2 = NULL,		           # chromosome 2, only useful when a heatmap is plotted
		     start = NULL,                         # start of region (string, may include Mb, kb, etc.)
		     end = NULL,                           # end of region (string, may include Mb, kb, etc.)
		     flank = "300kb",                      # surround refsnp by this much
		     xlabPos = -3.0,                       # position of xaxis label (in lines relative to bottom panel)
		     ylabPos = -3.5,                       # position of yaxis label (in lines relative to left edge of panel)
		     ylab = NULL,                            # override default label for y-axis
		     recombPos = 3.0,                      # position of recomb label (in lines relative to right edge of panel)
		     axisSize = 0.8,                         # sclaing factor for axes
		     axisTextSize = 0.8,                     # sclaing factor for axis labels
		     axisTextColor = "gray30",             # color of axis labels
		     requiredGene = NULL,                  # gene name (string)
		     refsnp = NULL,                        # snp name (string)
		     refsnpName = NULL,			  # name given to refsnp on plot (usually same as refsnp)
		     refsnpTextColor = "black",            # color for ref snp label
		     refsnpTextSize = 1,                   # sclaing factor for text size
		     refsnpTextAlpha = 1,                  # alpha for ref snp label
		     refsnpLineColor = "transparent",      # color for ref snp line (invisible by default)
		     refsnpLineAlpha = .5,                 # alpha for ref snp line
		     title = "",                           # title for plot
		     titleColor = "black",                 # color for title 
		     thresh = 1,                           # only get pvalues <= thresh   # this is now ignored.
		     width = 8.5,                           # width of pdf (inches)
		     height = 11,                           # height of pdf (inches)
		     leftMarginLines = 5,                  # margin (in lines) on left
		     rightMarginLines = 5,                 # margin (in lines) on right
		     unit=1000000,                         # bp per unit displayed in plot
		     ldTable = "results.ld_point6",        # LD Table (for SQL)
		     annot=NULL,                           # file for annotation 
		     showAnnot=FALSE,                      # show annotation for each snp?
		     showGenes=TRUE,                       # show genes?
		     annotCol='annotation',                # column to use for annotation, if it exists
		     annotPch='24,25,22,8,7,21,1',   # plot symbols for annotation
		     annotOrder=NULL,                      # ordering of annotation classes
		     annotName='annotationTitle',	      #title for annotation legend
		     showRefsnpAnnot=TRUE,                 # show annotation for reference snp too?
		     bigDiamond=FALSE,                     # put big diamond around refsnp?
		     ld=NULL,                              # file for LD information
		     ldCuts = "0,.2,.4,.6,.8,1",           # cut points for LD coloring
		     ldCutsForBarchart = "0,.1,.5,1",      # cut points for LD coloring in summarizing barchart
		     ldColors = "gray50,navy,lightskyblue,green,orange,red,purple3",  # colors for LD
		     ColorsForBarchart = "royalblue1,tomato",   #colors for LD in barchart
		     ldCol='rsquare',                      # name for LD column
		     LDTitle=NULL,                         # title for LD legend
		     smallDot = .4,                        # smallest p-value cex 
		     largeDot = .8,                        # largest p-value cex 
		     refDot = NULL,                        # largest p-value cex 
		     rfrows = '4',                         # max number of rows for reflat genes
		     warnMissingGenes = FALSE,             # should we warn about missing genese on the plot?
		     showPartialGenes = TRUE,              # should genes that don't fit completely be displayed?
		     shiftGeneNames = TRUE,                # should genes that don't fit completely be displayed?
		     geneFontSize = .8,                    # size for gene names
		     geneColor = "navy",                   # color for genes
		     snpset = "Affy500,Illu318,HapMap",    # SNP sets to show
		     snpsetFile = NULL,                    # use this file for SNPset data
		     rugColor = "gray30",                  # color for snpset rugs
		     rugAlpha = 1,                         # alpha for snpset rugs
		     metalRug = NULL,                      # if not null, use as label for rug of metal positions
		     refFlat = NULL,                       # use this file with refFlat info
		     showIso=FALSE,                        # show each isoform of gene separately
		     showRecomb = TRUE,                    # show recombination rate?
		     recomb=NULL,                          # rcombination rate file
		     recombAxisColor=NULL,                 # color for reccomb rate axis labeing
		     recombAxisAlpha=NULL,                 # color for reccomb rate axis labeing
		     recombColor='blue',                   # color for reccomb rate on plot
		     recombOver = FALSE,                   # overlay recombination rate? (else underlay it)
		     recombFill = FALSE,                   # fill recombination rate? (else line only)
		     recombFillAlpha=0.2,                  # recomb fill alpha
		     recombLineAlpha=0.8,                  # recomb line/text alpha
		     frameColor='gray30',                  # frame color for plots
		     frameAlpha=1,                         # frame alpha for plots
		     legendSize=.8,                        # scaling factor of legend
		     legendAlpha=1,                        # transparency of legend background
		     legendColor='black',                  # color for legend labels
		     legendMissing=TRUE,                   # show 'missing' as category in legend?
		     legend='auto',                        # legend? (auto, left, right, or none)
		     hiStart=0,                            # start of hilite region
		     hiEnd=0,                              # end of hilite region
		     hiColor="blue",                       # hilite color
		     hiAlpha=0.1,                          # hilite alpha
		     clobber=TRUE,                         # overwrite files?
		     reload=NULL,                          # .Rdata file to reload data from
		     prelude=NULL,                         # code to execute after data is read but before plot is made (allows data modification)
		     postlude=NULL,                        # code to execute after plot is made (allows annotation)
		     prefix=NULL,                          # prefix for output files
		     dryRun=FALSE                          # show a list of the arguments and then halt
		     )

### default data

refSnpPos <- data.frame()
recrate.default <- data.frame(chr=NA, pos=NA, recomb=NA, chr=NA, pos=NA)[c(),,drop=FALSE]
generic.default <- data.frame(chr=NA, start=NA, end=NA, score=NA)[c(),,drop=FALSE]
category.default <- data.frame(chr=NA,start=NA,end=NA,annotation=NA)[c(),,drop=FALSE]
rug.default <- data.frame(snp=NA, chr=NA, pos=NA, snp_set=NA)[c(),,drop=FALSE]
annot.default <- data.frame(snp=NA,annot_rank=NA) # [c(),,drop=FALSE]
ld.default <- data.frame(snp1='rs0000', snp2='rs0001', build=NA, 
			 chr=0, pos1=0, pos2=2, midpoint=1, distance=2, 
			 rsquare=0, dprime=0, r2dp=0) # [c(),,drop=FALSE]

refFlatRaw.default <- data.frame(geneName=NA, name=NA, chrom=NA, strand=NA, txStart=NA, txEnd=NA, 
				 cdsStart=NA, cdsEnd=NA, exonCount=NA, exonStarts=NA, exonEnds=NA, status=NA)[c(),,drop=FALSE]

#
# read and process command line arguments
#

user.args <- ConformList(argv(),names(default.args),message=TRUE)

default.args <- ProcessThemes(default.args,user.args[['theme']])

args <- ModifyList(default.args,user.args);

userFile <- list(
		 recomb = !is.null(args[['recomb']]),
		 generic = !is.null(args[['generic']]),
		 category = !is.null(args[['category']]),
		 snpsetFile = !is.null(args[['snpsetFile']]),
		 refFlat = !is.null(args[['refFlat']]),
		 ld = !is.null(args[['ld']]),
		 annot = !is.null(args[['annot']])
		 );

args <- MatchIfNull(args,'recombAxisAlpha','recombLineAlpha')
args <- MatchIfNull(args,'recombAxisColor','recombColor')
args <- AdjustModesOfArgs(args);

GetData <- GetDataFromFileIgnoreCommand
args[['showRefsnpAnnot']] <- args[['showAnnot']] & args[['showRefsnpAnnot']];

args[['refsnpColor']] <- args[['ldColors']][length(args[['ldColors']])];

if ( args[['dryRun']] )  {
    message("Argument list:");
    message(paste("\t",names(args),'=', args, "\n"));
    q();
}

#
# read metal data or reload all.
#

if ( is.null(args[['reload']]) ) {
    if ( file.exists( args[['metal']]) ) {
	metal <- read.file(args[['metal']]);
    } else {
	stop(paste('No such file: ', args[['metal']]));
    }
} else {
    if ( file.exists(args[['reload']]) ) {
	load( args[['reload']] );
	flags[['reloaded']] <- TRUE;
    } else {
	stop(paste("Stopping: Can't reload from", args[['reload']]));
    }
}
#
# column renaming in metal data.frame
#
if ( char2Rname(args[['pvalCol']]) %in% names(metal) ) {
    metal$P.value <- metal[ ,char2Rname(args[['pvalCol']]) ];
} else {
    stop(paste('No column named',args[['pvalCol']]));
}

transformation <- SetTransformation( min(metal$P.value,na.rm=TRUE), max(metal$P.value,na.rm=TRUE), 
				    args[['alreadyTransformed']] );

args[['LDTitle']] <- SetLDTitle( args[['ldCol']],args[['LDTitle']] )

if ( args[['posCol']] %in% names(metal) ) {
    metal$pos <- metal[ ,args[['posCol']] ];
} else {
    stop(paste('No column named',args[['posCol']]));
}

if ( char2Rname(args[['markerCol']]) %in% names(metal) ) {
    metal$MarkerName <- metal[ ,char2Rname(args[['markerCol']]) ];
} else {
    stop(paste('No column named',args[['markerCol']]));
}

#
# if no region and no refsnp specified, choose best snp and range of data set:
#
if ( (is.null(args[['start']]) || is.null(args[['end']]) || is.null(args[['chr']]) ) && ( is.null(args[['refsnp']]) ) ) 
{
    args[['start']] <- min(metal$pos);
    args[['end']] <- max(metal$pos);
    args[['chr']] <- min(metal$chr);
    args[['refsnp']] <- as.character( metal$MarkerName[ order(metal$P.value)[1] ] );

    args <- ModifyList(list(prefix=paste('chr',
					 args[['chr']],"_",args[['start']],"-",args[['end']],sep='')),
		       args);

    args <- ModifyList(list(prefix='foo'),args);
    flags[['flank']] <- FALSE;


    # if region but not refsnp, choose best snp as refsnp
} else if ( !is.null(args[['start']]) && !is.null(args[['end']]) && !is.null(args[['chr']]) && is.null(args[['refsnp']] ) ) 
{
    args <- ModifyList(
		       list( refsnp = as.character( metal$MarkerName[ order(metal$P.value)[1] ] ) ),
		       args
		       );
    flags[['flank']] <- FALSE;

    # if refsnp specifed but no region, select region flanking refsnp
} else if ( ( is.null(args[['start']]) || is.null(args[['end']]) || is.null(args[['chr']]) ) && (!is.null(args[['refsnp']]) ) ) 
{
    args <- ModifyList( args, list( flankBP=pos2bp(args[['flank']]) ) );

    refSnpPosFile <- paste(args[['refsnp']],"_pos.tbl",sep="");

    if ( is.null(refSnpPos) ) { args[['showRug']] = FALSE }
    refSnpPos <- GetData( refSnpPosFile, default=refSnpPos.default, clobber=TRUE);

    args[['refSnpPos']] <- as.character(refSnpPos$chrpos[1]);
    args[['refSnpBP']] <- pos2bp(refSnpPos$chrpos[1]);

    args <- ModifyList( args, list( start=args[['refSnpBP']] - args[['flankBP']] ) ) ;
    args <- ModifyList( args, list( end=args[['refSnpBP']] + args[['flankBP']] ) );
    args <- ModifyList( args, list( chr=refSnpPos$chr[1] ) );

    flags[['flank']] <- TRUE;

    # else refsnp and region specified
} else {  
    flags[['flank']] <- FALSE;
}

# change refsnp to "none" if it was null, else leave as is
args <- ModifyList( list( refsnp = "none"), args);

args <- ModifyList( args, list( start=as.character(args[['start']]) ) );
args <- ModifyList( args, list( end=as.character(args[['end']]) ) );

# prefix
if (flags[['flank']]) {
    args <- ModifyList(
		       list( prefix = paste(                   # #1
					    args[['refsnp']],
					    "_",   args[['flank']],
					    sep="")
		       ),
		       args
		       );
} else {
    args <- ModifyList(
		       list( prefix = paste(                   # #2
					    "chr", args[['chr']],
					    "_",   args[['start']],
					    "-",   args[['end']],
					    sep="")
		       ),
		       args
		       );
}

#log
args <- ModifyList(
		   list( log = paste(args[['prefix']], ".log", sep="") ),
		   args 
		   );

#recomb
args <- ModifyList(
		   list( recomb = paste(args[['prefix']], "_recomb", ".tbl", sep="") ),
		   args 
		   );
#generic
#args <- ModifyList(
#	list( generic = paste(args[['prefix']], "_generic", ".tbl", sep="") ),
#	args 
#	);
# annot
args <- ModifyList(
		   list( annot = paste(args[['prefix']], "_annot", ".tbl", sep="") ),
		   args 
		   );

# ld
args <- ModifyList(
		   list( ld = paste(args[['prefix']], "_ld", ".tbl", sep="") ),
		   args 
		   );

# snpsets
args <- ModifyList(
		   list( snpsetFile = paste(args[['prefix']], "_snpsets", ".tbl", sep="") ),
		   args 
		   );

# pdf
args <- ModifyList(
		   list( pdf = paste(args[['prefix']], ".pdf", sep="") ),
		   args
		   );

# rdata
args <- ModifyList(
		   list( rdata = paste(args[['prefix']], ".Rdata", sep="") ),
		   args
		   );

# refFlat
args <- ModifyList(
		   list( refFlat = paste(args[['prefix']], "_refFlat.txt", sep="") ),
		   args
		   );

args <- ModifyList(args, list( startBP=pos2bp(args[['start']]), endBP=pos2bp(args[['end']]) ));
args <- ModifyList(args, list( hiStartBP=pos2bp(args[['hiStart']]), hiEndBP=pos2bp(args[['hiEnd']]) ));

#######################################################
#
# now read other (non-metal) data
#
sink(args[['log']]);

if ( is.null(args[['reload']]) ) {

    # recombination rate

    if ( is.null(args[['recomb']])  ) { args[['showRecomb']] <- FALSE }
    tryCatch(
	     recrate <- GetData( args[['recomb']], default=recrate.default, 
				clobber=!userFile[['recomb']] || args[['clobber']] ),
	     error = function(e) { warning(e) }
	     )
    if ( prod(dim(recrate)) == 0 ) { args[['showRecomb']] <- FALSE }
    cat("\n\n");
    #generic score
    if ( is.null(args[['generic']]) ) { args[['showGeneric']] <- FALSE }
    if (args[['showGeneric']])
    {
	cat("\nR-DEBUG: Loading GENERIC annotation data...\n");
	generic_file_list = strsplit(args[['generic']],',')[[1]];
	generic_file_list = generic_file_list[generic_file_list != "None"];
	genscore=vector('list',length(generic_file_list));
	#naming
	print(2644);
	print(generic_file_list);
	print(genscore);
	for (i in 1:length(generic_file_list))
	{
	    genscore[[i]]=generic_file_list[i];
	    generic_file_list[i]=sub("[[:digit:]]+_[[:digit:]]+_","",generic_file_list[i]);
	    generic_file_list[i]=sub("\\.txt$","",generic_file_list[i]);
	    names(genscore)[i]=generic_file_list[i];
	}

	#read in data
	for (i in 1:length(names(genscore)) )
	{
	    tryCatch(
		     genscore[[i]] <-  GetData( genscore[[i]], default=generic.default, clobber=!userFile[['generic']] || args[['clobber']] ),
		     error = function(e) { warning(e) }
		     );
	    cat("\n\n");
	    #we will continue even if we got empty table
	    #if ( prod(dim(genscore[[i]])) == 0 )
	    #{

	    #    args[['showGeneric']] <- FALSE;
	    #    print (paste("Empty generic table: ",names(genscore)[i],sep=""));
	    #}
	}
    } else
    {
	genscore=NULL;
    }
    #category annotation
    if ( is.null(args[['category']]) ) {args[['showCategory']] <- FALSE }
    if (args[['showCategory']])
    {
	cat("\nR-DEBUG: Loading CATEGORICAL annotation data...\n");
	category_file_list = strsplit(args[['category']],',')[[1]];
	category_file_list = category_file_list[category_file_list != "None"];
	category_anno=vector('list',length(category_file_list));
	#naming
	for (i in 1:length(category_file_list))
	{
	    category_anno[[i]]=category_file_list[i];
	    category_file_list[i]=sub("[[:digit:]]+_[[:digit:]]+_","",category_file_list[i]);
	    category_file_list[i]=sub("\\.txt$","",category_file_list[i]);
	    names(category_anno)[i]=category_file_list[i];
	}

	#read in data
	for (i in 1:length(names(category_anno)) )
	{
	    tryCatch(
		     category_anno[[i]] <-  GetData( category_anno[[i]], default=category.default, clobber=!userFile[['category']] || args[['clobber']],stringsAsFactors=TRUE ),
		     error = function(e) { warning(e) }
		     );
	    cat("\n\n");
	    if ( prod(dim(category_anno[[i]])) == 0 )
	    {

		args[['showCategory']] <- FALSE;
		print (paste("Empty category annotation table: ",names(category_anno)[i],sep=""));
	    }
	}
    } else
    {
	category_anno=NULL;
    }


    #xyplot score
    if(!is.null(args[['xyplotCol']]))
    {
	cat("\nR-DEBUG: Processing XY plot data...\n");
	#naming
	if(length(unique(names(metal))) != length(names(metal)))
	{
	    stop("Column names in METAL must be unique!");
	}
	xyplotcol = unlist(strsplit(args[['xyplotCol']],','));
	if (length(which(xyplotcol %in% names(metal))) != length(xyplotcol))
	{
	    stop("Some XYPlot columns can NOT be found in METAL");
	}
	print(2674);
	print(str(metal));
	xyplotData = data.frame(apply(data.frame(metal[,xyplotcol]),2,as.numeric));
	print(str(xyplotData));
	colnames(xyplotData)=xyplotcol;#column names are not set automatically
	for (i in 1:length(names(xyplotData)))
	{
	    #convert string to numerical value, if in scientific notation, convert to plain decimal numbers
	    if ( !is.numeric(xyplotData[[i]]) )
	    {
		stop(paste(names(xyplotData)[i],"is not numeric"));
	    }
	}
	if (args[['xyplotlog']] == 'YES')
	{
	    xyplotData = log(xyplotData,10);
	} else if (args[['xyplotlog']] == 'MINUS')
	{
	    xyplotData = -log(xyplotData,10);
	} else if (args[['xyplotlog']] == 'NO')
	{
	    1;
	} else
	{
	    stop("Wrong xyplotlog option: YES, NO, MINUS only");
	}
	metal[,xyplotcol] = xyplotData;
	rm(xyplotcol,xyplotData);
    }

    #read in heatmap data
    if(!is.null(args[['heatmapFile']]))
    {
	cat("\nR-DEBUG: Processing heatmap data ...\n");
	
	#disable check.names to avoid unwanted changes in chr:pos-pos format
	heatmapRawData = GetData(args[['heatmapFile']],header=TRUE,check.names=FALSE);
	#example (header has one less field)
	#1:1-1000	1:1001-2000
	#1:1-1000	4.5	3.2
	#1:1001-2000	4.5	3.2

	print(2775);
	print(str(heatmapRawData));
	print(rownames(heatmapRawData));
	#use start point for each region
	#process rownames, they appear on x-axis,the first pos should be the start of first region, the last pos should be the end of last region
	#grep starts of regions
	rowpos1=regexpr(":[[:digit:]]+",rownames(heatmapRawData));
	rowpos1=substr(rownames(heatmapRawData),rowpos1+1,rowpos1+attr(rowpos1,"match.length")-1);
	#grep ends of regions
	rowpos2=regexpr("-[[:digit:]]+",rownames(heatmapRawData));
	rowpos2=substr(rownames(heatmapRawData),rowpos2+1,rowpos2+attr(rowpos2,"match.length")-1);
	#use starts as coordinates except the last one
	rownames(heatmapRawData)=rowpos1;
	rownames(heatmapRawData)[length(rowpos2)] = rowpos2[length(rowpos2)];
	#process colnames, they appear on y-axis
	colname_reg=regexpr("(?<chr>[[:digit:]]+):(?<pos1>[[:digit:]]+)-(?<pos2>[[:digit:]]+)",colnames(heatmapRawData),perl=TRUE);
	colpos1= substr(colnames(heatmapRawData),
		     attr(colname_reg,"capture.start")[,"pos1"],
		     attr(colname_reg,"capture.start")[,"pos1"]+attr(colname_reg,"capture.length")[,"pos1"]-1);
	colpos2= substr(colnames(heatmapRawData),
			attr(colname_reg,"capture.start")[,"pos2"],
			attr(colname_reg,"capture.start")[,"pos2"]+attr(colname_reg,"capture.length")[,"pos2"]-1);
	#use the middle point of each region as the Y coordinate on heatmap
	colnames(heatmapRawData)=(as.numeric(colpos1)+as.numeric(colpos2))/2
	heatmapData = expand.grid(chr1=as.numeric(rownames(heatmapRawData))/args[['unit']],chr2=as.numeric(colnames(heatmapRawData))/args[['unit']]);
	heatmapData$value = as.vector(t(heatmapRawData));
    } else
    {
        heatmapData = NULL;
    }

    # snpset positions

    rug <- GetData( args[['snpsetFile']], default=rug.default,
		   clobber=!userFile[['snpsetFile']] || args[['clobber']] );

    cat("\n\nsnpset summary:\n");
    print(summary(rug));
    cat("\n\n");
    # annotation
    if ( char2Rname(args[['annotCol']]) %in% names(metal) ) {  
	if (is.null(args[['annotOrder']])) {
	    args[['annotOrder']] <- 
		sort( unique( metal[,char2Rname(args[['annotCol']])] ) );
	}

	metal$annot <- MakeFactor(metal[,char2Rname(args[['annotCol']]) ], levels=args[['annotOrder']],
				  na.level='none')
	pchVals <- rep(args[['annotPch']], length=length(levels(metal$annot)));
	metal$pch <- pchVals[ as.numeric(metal$annot) ]
	annot <- metal$annot
    } 

    cat("\nR-DEBUG: Loading annotation data...\n");
    if( args[['showAnnot']] && ! 'pch'  %in% names(metal) ) { 
	if ( is.null(args[['annot']]) ) { args[['showAnnot']] <- FALSE }
	annot <- GetData( args[['annot']], annot.default,
			 clobber=!userFile[['annot']] || args[['clobber']] )
	if (prod(dim(annot)) == 0) { args[['showAnnot']] <- FALSE }
	cat("\nR-DEBUG: Merging in annotation data...");
	metal <- merge(metal, annot,  
		       by.x='MarkerName', by.y="snp",
		       all.x=TRUE, all.y=FALSE);
	cat(" Done.\n");
	print(head(metal));

	metal$annot <- 
	    c('no annotation','framestop','splice','nonsyn','coding','utr','tfbscons','mcs44placental')[1+metal$annot_rank];
	if ( is.null(args[['annotOrder']]) ) {
	    args[['annotOrder']] <- 
		c('framestop','splice','nonsyn','coding','utr','tfbscons','mcs44placental','no annotation')
	} 
	metal$annot <- MakeFactor(metal$annot, levels=args[['annotOrder']],na.level='none') 
	pchVals <- rep(args[['annotPch']], length=length(levels(metal$annot)));
	metal$pch <- pchVals[ as.numeric(metal$annot) ]

    }  else {

	if (! 'pch' %in% names(metal)) {
	    metal$pch <- 21;
	}

	if (! 'annot' %in% names(metal) ) {
	    metal$annot <- "none"
	    metal$annot <- factor(metal$annot)
	}
	annot <- data.frame();
    }

    if (FALSE) {  # scraps from above
	cat('else: ');
	pchVals <- rep(args[['annotPch']], length=length(levels(metal$annot)));
	metal$pch <- pchVals[ as.numeric(metal$annot) ]
	annot <- metal$annot
	print(xtabs(~annot+pch,metal));
	print(metal[1:4,])
    }


    sink('annotationTally.txt')
    print( args[['annotOrder']] )
    print(args[['annotPch']])
    print(args[['annotOrder']])
    print(table(metal$annot))
    print(table(metal$pch))
    print(xtabs(~annot+pch,metal))
    sink()
    # ld

    if ( is.null(args[['ld']])) { args[['legend']] = 'none' }
    ld <- GetData( args[['ld']], ld.default, 
		  clobber=!userFile[['ld']] || args[['clobber']] )
    cat("\n\n");




    if (! is.null(args[['metalRug']]) ) {
	metalRug <- data.frame(pos=metal$pos, snp_set=args[['metalRug']]);
	origRug <- data.frame(pos=rug$pos,snp_set=rug$snp_set)
	rug <- rbind(origRug,metalRug)
	print(levels(rug))
    }

    save(metal,annot,recrate,genscore,category_anno,ld,args,rug,heatmapData,file='loaded.Rdata');
    #save space

    if ( prod(dim(metal) ) < 1) { stop("No data read.\n"); }


    # subset the data
    s <- metal$pos >= args[['startBP']] & 
    metal$pos <= args[['endBP']] & 
    metal$chr == args[['chr']] ;
    # &  metal$P.value <= args[['thresh']];
    metal <- subset(metal, s);

    # merge LD info into metal data frame
    refSnp <- as.character(args[['refsnp']]);

    metal$group <- 1;
    metal$LD <- NA;
    metal$ldcut <- NA;
    metal$group[metal$MarkerName == refSnp] <- length(args[['ldColors']]);
    if (! is.null(ld)) 
    {
	# subset ld for reference SNP
	snpCols <- which(apply(ld,2,Sniff,type="snp"))
	if (length(snpCols) != 2) {
	    warning(paste("LD file doesn't smell right. (",
			  length(snpCols)," SNP cols)",sep=""))
	    assign("warningMessages",
		   c(warningMessages,"LD file doesn't smell right."), 
		   globalenv());
	    break;
	}
	w1 <- which ( ld[,snpCols[1]] == refSnp );
	w2 <- which ( ld[,snpCols[2]] == refSnp );
	c1 <- c(names(ld)[snpCols[1]],names(ld)[snpCols[2]],args[['ldCol']]); # "rsquare","dprime");
	c2 <- c(names(ld)[snpCols[2]],names(ld)[snpCols[1]],args[['ldCol']]); # "rsquare","dprime");
	ld1 <- ld[ w1, c1, drop=FALSE ]
	ld2 <- ld[ w2, c2, drop=FALSE ]
	names(ld1)[1:2] <- c("refSNP","otherSNP")
	names(ld2)[1:2] <- c("refSNP","otherSNP")
	lld <- rbind( ld1, ld2);
	if (prod(dim(lld)) > 0) { 
	    metal <- merge(metal, lld,  
			   by.x='MarkerName', by.y="otherSNP",
			   all.x=TRUE, all.y=FALSE);
	    if ( args[['ldCol']] %in% names(metal) ) {
		metal$LD <- metal[ ,args[['ldCol']] ];
	    } else {
		stop(paste('No column named',args[['ldCol']]));
	    }
	    metal$ldcut <- cut(metal$LD,breaks=args[['ldCuts']],include.lowest=TRUE);
	    metal$group <- 1 + as.numeric(metal$ldcut);
	    metal$group[is.na(metal$group)] <- 1;
	    metal$group[metal$MarkerName == refSnp] <- length(args[['ldColors']]) 
	} else {
	    assign("warningMessages",c(warningMessages,'No usable LD information for reference SNP.'), globalenv());
	    warning("No usable LD information.");
	    args[['legend']] <- 'none';
	}
    }
    save(metal,refSnp,args,file='temp.Rdata');

    if (is.null(args[['refFlat']]) ) { args[['showGenes']] <- FALSE }
    refFlatRaw <- GetData( args[['refFlat']], refFlatRaw.default,
			  clobber = !userFile[['refFlat']] || args[['clobber']] );

    summary(refFlatRaw);


    # subset the refFlatdata
    s <- refFlatRaw$txEnd >= args[['startBP']] & 
    refFlatRaw$txStart <= args[['endBP']] & 
    refFlatRaw$chrom == chr2chrom(args[['chr']]) ;
    refFlatRaw <- subset(refFlatRaw, s);
    save(refFlatRaw,args,file="refFlatRaw.Rdata");

    flatten.bed(refFlatRaw,multiplier=1/args[['unit']]) -> refFlat;
    summary(refFlat);

    # adjust for position units
    metal$pos <- metal$pos / args[['unit']];
    recrate$pos <- recrate$pos / args[['unit']];
    rug$pos <- rug$pos / args[['unit']];

    cat("recrate summary:\n");
    print(summary(recrate));
    cat("\n\n");
    cat("LD summary:\n");
    print(summary(ld));
    cat("\n\n");
    cat("metal summary:\n");
    print(summary(metal));
    cat("\n\n");
    if (! is.null(genscore))
    {
	cat("generic score summary");
	cat("\n\n");
	print(summary(genscore));
    }
    if (! is.null(category_anno))
    {
	cat("categorical annotation summary");
	cat("\n\n");
	print(summary(category_anno));
    }
    if (! is.null(heatmapData))
    {
	cat("heatmap data summary");
	cat("\n\n");
	print(summary(heatmapData));
    }


    save(metal,annot,recrate,genscore,category_anno,refFlatRaw,refFlat,rug,heatmapData,file=args[['rdata']]);
    #save space

} else {
    load(args[['rdata']]);
}

if (is.character(args[['prelude']]) && file.exists(args[['prelude']])) {
    source(args[['prelude']]);
}

if ( prod(dim(rug)) == 0 || !("snp_set" %in% names(rug)) ) {
    nrugs <- 0;
} else {
    nrugs <- length(levels(rug$snp_set));
}

xRange <- range(metal$pos,na.rm=T);
xRange <- as.numeric(c(args[['start']],args[['end']])) / args[['unit']];
refFlat <- refFlat[ which( (refFlat$start <= xRange[2]) & (refFlat$stop >= xRange[1]) ), ]
yRange <- c(min(c(args[['ymin']],transformation(metal$P.value),na.rm=T)),
	    min(c(args[['ymax']],1+ceiling(max(transformation(metal$P.value)*1.1))),na.rm=T));

recrateRange <- c(0,max(c(100,recrate$recomb),na.rm=T));
if (args[['experimental']]) { 
    recrate$recomb <- max(c(100,recrate$recomb),na.rm=T) - recrate$recomb;
    recrateRange <- c(0,max(c(100,recrate$recomb),na.rm=T));
}

recrateRange <- rev(recrateRange);
print("recrateRange: ");
print(recrateRange);

refSnp <- as.character(args[['refsnp']]);
refidx <- match(refSnp, metal$MarkerName);
if (!args[['showRefsnpAnnot']]) {
    metal$pch[refidx] <- 23;  # use a diamond for ref snp
}
if ('pdf' %in% args[['format']]) {
    pdf(file=args[['pdf']],width=args[['width']],height=args[['height']],version='1.4',onefile=TRUE);
    if ( prod(dim(metal)) == 0 ) { 
	message ('No data to plot.'); 
    } else {
	zplot(metal,ld,recrate,genscore,category_anno,refidx,nrugs=nrugs,args=args,heatmapData=heatmapData,postlude=args[['postlude']]);
	grid.newpage();
    }
    print("metal content");
    print(metal);
    grid.log(args,metal);
    grid.summary(args,metal,genscore,category_anno);
    dev.off();
} 

sink(args[['log']], append=TRUE);
cat('\n\n\n');
cat("List of genes in region\n");
cat("#######################\n");
geneList <- make.gene.list(refFlat,unit=args[['unit']]);
if (! is.null(geneList)) {
    digits <- 7 + ceiling(log10(max(geneList$stop)));
    print(geneList,digits=digits);
}
cat('\n\n\n');
sink();

save(metal,refFlat,ld,recrate,refSnpPos,args,genscore,category_anno,file='end.Rdata');
CleanUp(args,refSnpPos,recrate,rug,ld,refFlatRaw,genscore,category_anno);

date();
