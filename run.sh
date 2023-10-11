NUM_TESTS=1000
PARALLEL=32
MUTATION_NUMBER=1000
OUTDIR=output/

rm -rf $OUTDIR
seq -w 1 $NUM_TESTS | xargs -n 1 -P $PARALLEL -I {} bash -c "python3 main.py $OUTDIR {} $MUTATION_NUMBER"