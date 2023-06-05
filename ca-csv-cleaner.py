#!/usr/bin/env python3

import csv

file = open('bank.csv', newline='', encoding="iso-8859-1")
output_file = open('output.csv', "w")
payees_file = open('payees.txt', newline='')

payees = dict()

for entry in payees_file:
   entry = entry.strip()

   if (entry.startswith("#")):
      continue

   if (len(entry) == 0):
      continue

   data = entry.split(",")

   for alias in data[1:]:
      payees[alias] = data[0]
      print(
         "[D] Loaded payee \""
         + data[0]
         + "\" alias \""
         + alias
         + "\"."
      )

payees_file.close()

reader = csv.reader(file, delimiter=';')

entries = []

for row in reader:
   if (len(row) == 0):
      continue
   elif (len(row) != 5):
      print(
         "[W] Unexpected entry \""
         + str(row)
         + "\". Expected 5 values, not "
         + str(len(row))
         + "."
      )
   else:
      date = row[0]
      desc = row[1]
      lost = row[2]
      gained = row[3]
      unknown = row[4]

      buffer = desc.split('\n')

      i = 0

      while (i < len(buffer)):
         buffer[i] = buffer[i].strip()

         if (len(buffer[i]) == 0):
            del buffer[i]
         else:
            i += 1

      payee = desc

      if (buffer[0] == "PAIEMENT PAR CARTE"):
         data = buffer[1].split(" ")
         payee = " ".join(data[1:(len(data) - 1)]).strip()
      else:
         for k in payees.keys():
            if (k in desc):
               payee = payees[k]
               break

      output_file.write(date)
      output_file.write(";")
      output_file.write(payee)
      output_file.write(";")
      output_file.write(desc)
      output_file.write(";")
      output_file.write(lost)
      output_file.write(";")
      output_file.write(gained)
      output_file.write(";")
      output_file.write(unknown)
      output_file.write(";")
      output_file.write("\n")
output_file.close()
file.close()
