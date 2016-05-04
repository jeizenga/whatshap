from nose.tools import raises
from whatshap.core import DPTable, ReadSet, PedigreeDPTable, Pedigree
from .phasingutils import string_to_readset, brute_force_phase


def test_phase_empty_readset():
	rs = ReadSet()
	dp_table = DPTable(rs, all_heterozygous=False)
	superreads = dp_table.get_super_reads()


def compare_phasing_brute_force(superreads, cost, partition, readset, all_heterozygous, weights = None):
	"""Compares DPTable based phasing to brute force phasing and returns string representation of superreads."""
	assert len(superreads) == 2
	assert len(superreads[0]) == len(superreads[1])
	for v1, v2 in zip(*superreads):
		assert v1.position == v2.position
	haplotypes = tuple(sorted(''.join(str(v.allele) for v in sr) for sr in superreads))
	expected_cost, expected_partition, solution_count, expected_haplotype1, expected_haplotype2 = brute_force_phase(readset, all_heterozygous)
	inverse_partition = [1-p for p in partition]
	print()
	print(superreads[0])
	print(superreads[1])
	print('Partition:', partition)
	print('Expected: ', expected_partition)
	print('Haplotypes:')
	print(haplotypes[0])
	print(haplotypes[1])
	print('Expected Haplotypes:')
	print(expected_haplotype1)
	print(expected_haplotype2)
	print('Cost:', cost)
	print('Expected cost:', expected_cost)
	assert (partition == expected_partition) or (inverse_partition == expected_partition)
	assert solution_count == 1
	assert cost == expected_cost
	assert (haplotypes == (expected_haplotype1, expected_haplotype2)) or (haplotypes == (expected_haplotype2, expected_haplotype1))


def check_phasing_single_individual(reads, weights = None):
	# 0) set up read set
	readset = string_to_readset(reads, weights)
	positions = readset.get_positions()

	# 1) Phase using classic (RECOMB 2014 / wMEC) single individual phasing code
	#    TODO: Remove once phasing code has been unified+tested with PedMEC (including all_het mode off)
	for all_heterozygous in [False, True]: 
		dp_table = DPTable(readset, all_heterozygous)
		superreads = dp_table.get_super_reads()
		cost = dp_table.get_optimal_cost()
		partition = dp_table.get_optimal_partitioning()
		compare_phasing_brute_force(superreads, cost, partition, readset, all_heterozygous, weights)
	
	# 2) Phase using PedMEC code for single individual
	read_sources = [0] * len(readset) # all reads from the child
	recombcost = [1] * len(positions) # recombination costs 1, should not occur 
	pedigree = Pedigree()
	pedigree.add_individual(0, [1] * len(positions)) # all genotypes heterozygous
	dp_table = PedigreeDPTable(readset, read_sources, recombcost, pedigree)
	superreads, transmission_vector = dp_table.get_super_reads()
	# TODO: transmission vectors not returned properly, see issue 73
	assert len(set(transmission_vector)) == 1
	partition = dp_table.get_optimal_partitioning()
	compare_phasing_brute_force(superreads[0], cost, partition, readset, True, weights)

	# 3) Phase using PedMEC code for trios with two "empty" individuals (i.e. having no reads)
	read_sources = [0] * len(readset) # all reads from the child
	recombcost = [1] * len(positions) # recombination costs 1, should not occur 
	pedigree = Pedigree()
	pedigree.add_individual(0, [1] * len(positions)) # all genotypes heterozygous
	pedigree.add_individual(1, [1] * len(positions)) # all genotypes heterozygous
	pedigree.add_individual(2, [1] * len(positions)) # all genotypes heterozygous
	pedigree.add_relationship(0, 1, 2)
	dp_table = PedigreeDPTable(readset, read_sources, recombcost, pedigree)
	superreads, transmission_vector = dp_table.get_super_reads()
	assert len(set(transmission_vector)) == 1
	partition = dp_table.get_optimal_partitioning()
	compare_phasing_brute_force(superreads[0], cost, partition, readset, True, weights)


def test_phase_trivial() :
	reads = """
          11
           1
           01
        """
	check_phasing_single_individual(reads)


def test_phase1():
	reads = """
	 10
	 010
	 010
	"""
	check_phasing_single_individual(reads)


def test_phase2():
	reads = """
	  1  11010
	  00 00101
	  001 0101
	"""
	check_phasing_single_individual(reads)


def test_phase3():
	reads = """
	  1  11010
	  00 00101
	  001 01010
	"""
	check_phasing_single_individual(reads)


def test_phase4():
	reads = """
	  1  11010
	  00 00101
	  001 01110
	   1    111
	"""
	check_phasing_single_individual(reads)


def test_phase4():
	reads = """
	  1  11010
	  00 00101
	  001 01110
	   1    111
	"""
	check_phasing_single_individual(reads)


def test_phase5():
	reads = """
	  0             0
	  110111111111
	  00100
	       0001000000
	       000
	        10100
	              101
	"""
	check_phasing_single_individual(reads)


def test_weighted_phasing1():
	reads = """
	  1  11010
	  00 00101
	  001 01110
	   1    111
	"""
	weights = """
	  2  13112
	  11 23359
	  223 56789
	   2    111
	"""
	check_phasing_single_individual(reads, weights)
