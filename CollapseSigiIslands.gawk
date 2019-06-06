BEGIN { 
    FS=OFS="\t";
    inIsland = 0; # Flag to track that the next record is part of the same island
    print "##gff-version 3";
}
/^#/ { print; next; }
$4 == "1" || $5 == "0" { next } # Some results contain lines where start is 1 / end is 0. Skip to avoid erroneous GIs
$3 == "PUTAL" && !inIsland { 
    sub(/;$/, "", $1) # Remove trailing garbage SigiHMM attaches to id
    id=$1; src=$2; start=$4; end=$5;
    inIsland=1;
    next;
}
$3 == "PUTAL" && inIsland { end=$5; next }
$3 != "PUTAL" && inIsland { print id, src, "genomic_island", start, end, ".", ".", ".", ""; inIsland=0; }
END { if (inIsland) print id, src, "genomic_island", start, end, ".", ".", ".", ""; }
