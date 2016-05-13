from __future__ import unicode_literals, absolute_import, print_function
"""
Example usage of the Nef reader.

First, we'll use the conveniance function `open` to read one of the test files from disk.
Then, we'll explore the file and find some data.

"""
from ..NEFreader.nef import Nef

if __name__ == '__main__':
  nef_file = 'tests/test_files/CCPN_2l9r_Paris_155.nef'
  paris = Nef.from_file('tests/test_files/CCPN_2l9r_Paris_155.nef')

  # Get the data block name
  print('Data Block name: {}'.format(paris.datablock))
  print()


  # List the saveframes and their categories
  print ('Saveframes : categories')
  for k in paris.keys():
      category = paris[k]['sf_category']
      print(k, ':', category)
  print()


  # List the information available in the `sequence` loop of the nef_molecular_system saveframe
  print('nef_molecular_system;sequence columns')
  print(list(paris['nef_molecular_system']['nef_sequence'][0].keys()))
  print()


  # List the 3 letter codes for the sequence
  nef_sequence_loop = paris['nef_molecular_system']['nef_sequence']
  seq = [s['residue_type'] for s in nef_sequence_loop]
  print('3 letter sequence')
  print(seq)
  print()


  # Get the H, N shifts
  # This code can be simplified, but is here to demonstrate access rather than production code
  cs_loop = paris['nef_chemical_shift_list_bmrb21.str']['nef_chemical_shift']
  aa_number_column = [row['sequence_code'] for row in cs_loop]
  aa_type_column = [row['residue_type'] for row in cs_loop]
  atom_name_column = [row['atom_name'] for row in cs_loop]
  cs_column = [row['value'] for row in cs_loop]
  rows = zip(aa_number_column,
             aa_type_column,
             atom_name_column,
             cs_column)

  h_or_n_shifts = [row for row in rows if row[2] in ('H','N')]

  first_aa = int(min(aa_number_column))
  last_aa = int(max(aa_number_column))

  shifts = {i:['.', '.','.'] for i in range(first_aa, last_aa+1)}

  for shift in h_or_n_shifts:
      k = int(shift[0])
      shifts[k][0] = shift[1]
      if shift[2] == 'H':
          shifts[k][1] = float(shift[3])
      elif shift[2] == 'N':
          shifts[k][2] = float(shift[3])

  print('#  | Type |   H   |   N   |')
  fmt = '{:<4} {:<4}  {:<3}   {:>4}'
  for k,v in shifts.items():
      print(fmt.format(k,*v))
  print()


  # Get the H, N shifts, but using pandas
  try:
      import numpy as np
      import pandas as pd

      cs_loop = paris['nef_chemical_shift_list_bmrb21.str']['nef_chemical_shift']
      df = pd.DataFrame(cs_loop)
      df.replace({'.': np.NAN, 'true': True, 'false': False}, inplace=True)
      atom_names_to_use = list(df['atom_name'].unique())

      first_aa = int(df['sequence_code'].min())
      last_aa = int(df['sequence_code'].max())

      # make an empty dataframe with the correct column names
      df_merged = pd.DataFrame(index=range(first_aa, last_aa+1),
                               columns=['type']+atom_names_to_use)
      df_merged.index = df_merged.index.astype(str) # NEF sequence_codes are strings

      # now fill in our empty data frame
      for atom_name in atom_names_to_use:
          df_atom_type = df[df['atom_name']==atom_name]
          df_atom_type = df_atom_type.set_index('sequence_code')
          df_atom_type = df_atom_type.rename(columns={'residue_type':'type', 'value':atom_name})
          df_merged.update(df_atom_type)

      print(df_merged[['type', 'H', 'N']])
      print()
      # Optionally you can replace the NA values with `.`
      print(df_merged[['type', 'H', 'N']].fillna('.'))
      print()


  # Or the fancy pandas way that does everything, then select what to print at the end
      cs_loop = paris['nef_chemical_shift_list_bmrb21.str']['nef_chemical_shift']
      df = pd.DataFrame(cs_loop)

      pvt_values = df[['sequence_code','atom_name','value']]\
                      .pivot(index='sequence_code', columns='atom_name')
      pvt_values.columns = pvt_values.columns.droplevel(0)

      pvt_uncertainties = df[['sequence_code','atom_name','value_uncertainty']]\
                             .pivot(index='sequence_code', columns='atom_name')
      pvt_uncertainties.columns = pvt_uncertainties.columns.droplevel(0)

      pvt = pvt_values.join(pvt_uncertainties,rsuffix='_uncertainty')

      res_types = df.drop('atom_name', axis=1)
      res_types = res_types.drop_duplicates('sequence_code')
      res_types = res_types.set_index('sequence_code', drop=True)

      pvt = pvt.join(res_types)
      pvt = pvt.rename(columns={'residue_type': 'type',
                                'chain_code': 'chain'})

      print(pvt[['type', 'H', 'H_uncertainty', 'N', 'N_uncertainty']].fillna('.'))

  except ImportError:
      pass
