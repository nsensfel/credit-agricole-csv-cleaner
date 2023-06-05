#!/usr/bin/env python3

import argparse
import csv
import sys
import os

################################################################################
#### ARGPARSE CONFIGURATION ####################################################
################################################################################
argument_parser = (
   argparse.ArgumentParser(
      prog='ca-csv-cleaner.py',
      description='Utility to cleanup Credit Agricole operations.',
      epilog='Go to https://github.com/nsensfel/credit-agricole-csv-cleaner for help.'
   )
)

argument_parser.add_argument(
   'CSV_OPERATION_FILE',
   action='store',
   nargs=1,
   help='CSV file to parse.'
)

argument_parser.add_argument(
   '-p',
   '--payees',
   action='store',
   nargs=1,
   help='File containing payees info.'
)

argument_parser.add_argument(
   '-m',
   '--store-missing-to',
   action='store',
   nargs=1,
   help='Transactions without payees will be copied there.'
)

argument_parser.add_argument(
   '-o',
   '--output-file',
   action='store',
   nargs=1,
   help='Output file. Defaults to a suffix of the input file.'
)

argument_parser.add_argument(
   '-l',
   '--store-logs-to',
   action='store',
   nargs=1,
   help='Stores all console messages to the file.'
)

parsed_arguments = argument_parser.parse_args()

################################################################################
#### CONSOLE OUTPUT ############################################################
################################################################################
class ConsoleOut:
   log_file = None
   enable_debug_messages = False
   warnings = 0
   errors = 0

   def set_log_file (filename):
      if (ConsoleOut.log_file is not None):
         ConsoleOut.log_file.close()

      ConsoleOut.log_file = open(filename, 'w')

   def enable_debug_messages ():
      ConsoleOut.enable_debug_messages = True

   def close ():
      ConsoleOut.standard(
         "Completed with "
         + str(ConsoleOut.errors)
         + " error(s) and "
         + str(ConsoleOut.warnings)
         + " warning(s)."
      )

      if (ConsoleOut.log_file is not None):
         ConsoleOut.standard(
            "Logs available in "
            + str(os.path.realpath(ConsoleOut.log_file.name))
            + "."
         )
         ConsoleOut.log_file.close()

   def handle_message (tag, message, stdout):
      message = tag + (" " if (len(tag) > 0) else "") + message

      if (ConsoleOut.log_file is not None):
         ConsoleOut.log_file.write(message)
         ConsoleOut.log_file.write("\n")

      print(message, file = stdout)

   def error (message):
      ConsoleOut.errors = ConsoleOut.errors + 1
      ConsoleOut.handle_message("[E]", message, sys.stderr)

   def warning (message):
      ConsoleOut.warnings = ConsoleOut.warnings + 1
      ConsoleOut.handle_message("[W]", message, sys.stderr)

   def fatal (message):
      ConsoleOut.handle_message("[F]", message, sys.stderr)
      ConsoleOut.close()
      os.exit(-1)

   def debug (message):
      if (ConsoleOut.enable_debug_messages):
         ConsoleOut.handle_message("[D]", message, sys.stdout)

   def standard (message):
      ConsoleOut.handle_message('', message, sys.stdout)

################################################################################
#### SCRIPT ####################################################################
################################################################################
if (parsed_arguments.store_logs_to is not None):
   ConsoleOut.set_log_file(parsed_arguments.store_logs_to[0])

try:
   input_file = (
      open(
         parsed_arguments.CSV_OPERATION_FILE[0],
         newline='',
         encoding="iso-8859-1"
      )
   )
except IOError as e:
   ConsoleOut.fatal(
      "Could not open CSV operation file \""
      + parsed_arguments.csv_operation_file[0]
      + "\": "
      + e.strerror
   )
except:
   ConsoleOut.fatal(
      "Could not open CSV operation file \""
      + parsed_arguments.csv_operation_file[0]
      + "\": "
      + sys.exc_info()[0]
   )

if (parsed_arguments.output_file is not None):
   output_filename = parsed_arguments.output_file[0]
else:
   output_filename = (
      parsed_arguments.CSV_OPERATION_FILE[0]
      + ".cleaned.csv"
   )

try:
   output_file = open(output_filename, "w")
except IOError as e:
   ConsoleOut.fatal(
      "Could not create output file \""
      + output_filename
      + "\": "
      + e.strerror
   )
except:
   ConsoleOut.fatal(
      "Could not create output file \""
      + output_filename
      + "\": "
      + sys.exc_info()[0]
   )

missing_payee_file = None

if (parsed_arguments.store_missing_to is not None):
   try:
      missing_payee_file = open(parsed_arguments.store_missing_to[0], "w")
   except IOError as e:
      ConsoleOut.fatal(
         "Could not create storage for missing payees \""
         + parsed_arguments.store_missing_to[0]
         + "\": "
         + e.strerror
      )
   except:
      ConsoleOut.fatal(
         "Could not create storage for missing payees \""
         + parsed_arguments.store_missing_to[0]
         + "\": "
         + str(sys.exc_info()[0])
      )

payees = dict()

if (parsed_arguments.payees is not None):
   try:
      payees_file = open(parsed_arguments.payees[0], newline='')
   except IOError as e:
      ConsoleOut.fatal(
         "Could not open payees file \""
         + parsed_arguments.payees[0]
         + "\": "
         + e.strerror
      )
   except:
      ConsoleOut.fatal(
         "Could not open payees file \""
         + parsed_arguments.payees[0]
         + "\": "
         + str(sys.exc_info()[0])
      )

   for entry in payees_file:
      entry = entry.strip()

      if (entry.startswith("#")):
         continue

      if (len(entry) == 0):
         continue

      data = entry.split(",")

      if (len(data) < 2):
         ConsoleOut.error(
            "Ignoring invalid payee entry in \""
            + parsed_arguments.payees[0]
            + "\": "
            + entry
         )
         continue

      for alias in data[1:]:
         payees[alias] = data[0]
         ConsoleOut.debug(
            "Loaded payee \""
            + data[0]
            + "\" alias \""
            + alias
            + "\"."
         )

   payees_file.close()

reader = csv.reader(input_file, delimiter=';')

entries = []

unknown_payees = 0

for row in reader:
   if (len(row) == 0):
      continue
   elif (len(row) != 5):
      ConsoleOut.warning(
         "Unexpected entry \""
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

      found_payee = False

      if (buffer[0] == "PAIEMENT PAR CARTE"):
         data = buffer[1].split(" ")
         payee = " ".join(data[1:(len(data) - 1)]).strip()
         found_payee = True
      else:
         for k in payees.keys():
            if (k in desc):
               payee = payees[k]
               found_payee = True
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

      if (not found_payee):
         unknown_payees += 1

         if (missing_payee_file is not None):
            missing_payee_file.write(date)
            missing_payee_file.write(";")
            missing_payee_file.write(desc)
            missing_payee_file.write(";")
            missing_payee_file.write("\n")

if (missing_payee_file is not None):
   missing_payee_file.close()

if (unknown_payees > 0):
   ConsoleOut.warning(
      "There were "
      + str(unknown_payees)
      + " transactions with unknown payees"
      + (
         "." if (missing_payee_file is None) else (
            ". See \""
            + parsed_arguments.store_missing_to[0]
            + "\" for a full list."
         )
      )
   )

output_file.close()
input_file.close()
ConsoleOut.close()
