import type {UserConfig} from '@commitlint/types'; 

const Configuration: UserConfig = {

  extends: ['@commitlint/config-conventional'],

  rules: {

    // 'type-enum': [RuleConfigSeverity.Error, 'always', ['foo']],

    'type-enum' : [

        2,

        'always',

        [

            'feat',   //New features

            'fix',    // Bug fixes

            'chore',  // Maintenance tasks

            'ci',     //CI configuration changes

            'docs',    //Documentation updates

            'perf',   // Performance Improvements

            'refactor',   // Code Refactoring

            'revert',   //Revert to previous commit

            'style',   // Code style changes

            'test',   // Adding or Updating tests
            
            //other rules as required

        ],

    ] ,

  },

};

module.exports = Configuration;