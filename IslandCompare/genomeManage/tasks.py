from __future__ import absolute_import
from IslandCompare.celery import app
from celery import shared_task
from genomeManage.models import Genome, Job, MauveAlignment, SigiHMMOutput, Parsnp
from django.conf import settings
from genomeManage.libs import mauvewrapper, sigihmmwrapper, parsnpwrapper, fileconverter
from Bio import SeqIO
import os

@shared_task
def parseGenbankFile(sequenceid):
    # Parses a Genomes gbk file and updates the database with data from the file
    # Takes the genomes sequenceid (primary key) and returns None
    # Currently updates the name of the genome in the database
    # Also creates an embl file and faa file from the gbk file
    sequence=Genome.objects.get(id=sequenceid)
    for record in SeqIO.parse(open(settings.MEDIA_ROOT+"/"+sequence.genbank.name),"genbank"):
        sequence.name = record.id
        sequence.length = len(record.seq)
        sequence.description = record.description
        break
    SeqIO.convert(settings.MEDIA_ROOT+"/"+sequence.genbank.name, "genbank",
                  settings.MEDIA_ROOT+"/embl/"+sequence.name+".embl", "embl")
    sequence.embl = settings.MEDIA_ROOT+"/embl/"+sequence.name+".embl"
    sequence.faa = fileconverter.convertGbkToFna(settings.MEDIA_ROOT+"/"+sequence.genbank.name,
                                                 settings.MEDIA_ROOT+"/faa/"+sequence.name+".fna")
    sequence.save()

@shared_task
def runMauveAlignment(jobId,sequenceIdList):
    # Given a jobId and a list of genomeIds this will run Mauve on the input genomes gbk files
    # On start, job status will be updated to running in the database and will change on completion of function
    currentJob = Job.objects.get(id=jobId)
    currentJob.status = 'R'
    currentJob.save()
    sequencePathList = []
    outputfilename = settings.MEDIA_ROOT+"/mauve/"+("-".join(sequenceIdList))
    for genomeid in sequenceIdList:
        currentGenome = Genome.objects.get(id=genomeid)
        sequencePathList.append(settings.MEDIA_ROOT+"/"+currentGenome.genbank.name)

    try:
        mauvewrapper.runMauve(sequencePathList,outputfilename)
        mauvealignmentjob = MauveAlignment.objects.get(jobId=currentJob)
        mauvealignmentjob.backboneFile = outputfilename+".backbone"
        mauvealignmentjob.save()
        currentJob.status = 'C'
    except:
        currentJob.status = 'F'
    currentJob.save()

@shared_task
def runSigiHMM(sequenceId):
    # Given a genomeIds this will run SigiHMM on the input genome file
    currentGenome = Genome.objects.get(id=sequenceId)
    outputbasename = settings.MEDIA_ROOT+"/sigi/"+currentGenome.name
    sigihmmwrapper.runSigiHMM(currentGenome.embl.name,
                              outputbasename+".embl",outputbasename+".gff")
    sigi = SigiHMMOutput(embloutput=outputbasename+".embl",gffoutput=outputbasename+".gff")
    sigi.save()
    currentGenome.sigi = sigi
    currentGenome.save()

@shared_task
def runParsnp(jobId, sequenceIdList):
    # Given a jobId and sequenceIdList, this will create an output directory in the parsnp folder and
    # fill it with the output created by running parsnp
    # this will also update the parsnp job in the database to have the path to the tree file
    outputDir = settings.MEDIA_ROOT+"/parsnp/"+str(jobId)
    os.mkdir(outputDir)
    faaInputList = []
    for sequenceId in sequenceIdList:
        seq = Genome.objects.get(id=sequenceId)
        faaInputList.append(seq.faa.name)
    parsnpwrapper.runParsnp(faaInputList,outputDir)
    currentJob = Job.objects.get(id=jobId)
    parsnpjob = Parsnp.objects.get(jobId=currentJob)
    parsnpjob.treeFile = outputDir+"/parsnp.tree"
    parsnpjob.save()