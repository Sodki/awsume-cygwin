import sys, os
import unittest
import collections
import datetime
import argparse
import mock
import copy
import StringIO
import boto3
from awsume import awsumepy

    #parse_arguments
    #handle_command_line_arguments
    #get_profiles_from_ini_file
    #get_ini_profile_by_name
    #get_config_profile
    #get_credentials_profile
    #validate_profiles
    #handle_profiles
    #get_awsume_user_credentials
    #get_awsume_role_credentials
    #start_auto_refresher
    #handle_getting_role_credentials
    #validate_credentials_profile
    #get_source_profile_from_role
    #is_role_profile
    #read_mfa
    #is_valid_mfa_token
    #create_boto_sts_client
    #get_session_token_credentials
    #get_assume_role_credentials
    #create_awsume_session
    #session_string
    #parse_session_string
    #write_awsume_session_to_file
    #read_awsume_session_from_file
    #is_valid_awsume_session
    #write_auto_awsume_session
#kill_all_auto_processes
#remove_all_auto_profiles
#remove_auto_awsume_profile_by_name
#is_auto_refresh_profiles
#stop_auto_refresh
#generate_formatted_data
#print_formatted_data
#list_profile_data

class TestParseArguments(unittest.TestCase):
    def test_parse_arguments(self):
        #various command-line flags
        defaultFlag = '-d'
        showFlag = '-s'
        refreshFlag = '-r'
        autoRefreshFlag = '-a'
        killAutoRefresherFlag = '-k'
        versionFlag = '-v'
        listProfilesFlag = '-l'

        #normal use-cases
        self.assertTrue(awsumepy.parse_arguments([defaultFlag]).default)
        self.assertTrue(awsumepy.parse_arguments([showFlag]).show)
        self.assertTrue(awsumepy.parse_arguments([refreshFlag]).refresh)
        self.assertTrue(awsumepy.parse_arguments([autoRefreshFlag]).auto_refresh)
        self.assertTrue(awsumepy.parse_arguments([killAutoRefresherFlag]).kill)
        self.assertTrue(awsumepy.parse_arguments([versionFlag]).version)
        self.assertTrue(awsumepy.parse_arguments([listProfilesFlag]).list_profiles)
        self.assertEqual(awsumepy.parse_arguments(['input_name']).profile_name, 'input_name')

        #invalid inputs will exit
        with self.assertRaises(SystemExit) as cm:
            awsumepy.parse_arguments(['one_name', 'two_name'])
        self.assertEqual(cm.exception.code, 2)

class TestPrintVersion(unittest.TestCase):
    def test_print_version(self):
        capturedOut = StringIO.StringIO()
        sys.stdout = capturedOut
        awsumepy.print_version()
        sys.stdout = sys.__stdout__
        self.assertEqual(capturedOut.getvalue(), 'Version ' + awsumepy.__version__ + '\n')

class TestSetDefaultProfile(unittest.TestCase):
    def test_set_default_profile(self):
        args = argparse.Namespace()
        awsumepy.set_default_profile(args)

        self.assertTrue(args.default)
        self.assertEqual(args.profile_name, 'default')

class TestHandleCommandLineArguments(unittest.TestCase):
    @mock.patch('awsume.awsumepy.set_default_profile')
    @mock.patch('awsume.awsumepy.stop_auto_refresh')
    @mock.patch('awsume.awsumepy.list_profile_data')
    @mock.patch('awsume.awsumepy.print_version')
    def test_handle_command_line_arguments(self,
                                           mock_print_version,
                                           mock_list_profile_data,
                                           mock_stop_auto_refresh,
                                           mock_set_default_profile):

        emptyArgs = argparse.Namespace()
        emptyArgs.version = False
        emptyArgs.list_profiles = False
        emptyArgs.kill = False
        emptyArgs.default = False
        emptyArgs.profile_name = None

        versionArgs = copy.copy(emptyArgs)
        versionArgs.version = True
        with self.assertRaises(SystemExit):
            awsumepy.handle_command_line_arguments(versionArgs)

        listProfileArgs = copy.copy(emptyArgs)
        listProfileArgs.list_profiles = True
        with self.assertRaises(SystemExit):
            awsumepy.handle_command_line_arguments(listProfileArgs)

        killArgs = copy.copy(emptyArgs)
        killArgs.kill = True
        with self.assertRaises(SystemExit):
            awsumepy.handle_command_line_arguments(killArgs)

        defaultArgs = copy.copy(emptyArgs)
        defaultArgs.default = True
        defaultProfileArgs = copy.copy(emptyArgs)
        defaultProfileArgs.profile_name = "default"
        awsumepy.handle_command_line_arguments(defaultArgs)
        awsumepy.handle_command_line_arguments(defaultProfileArgs)
        awsumepy.handle_command_line_arguments(emptyArgs)

        self.assertEqual(mock_print_version.call_count, 1)
        self.assertEqual(mock_stop_auto_refresh.call_count, 1)
        self.assertEqual(mock_list_profile_data.call_count, 1)
        self.assertEqual(mock_set_default_profile.call_count, 3)

class TestGetProfilesFromINIFile(unittest.TestCase):
    @mock.patch('ConfigParser.ConfigParser')
    @mock.patch('os.path.exists')
    def test_get_profiles_from_ini_file(self, mock_os_path_exists, mock_config_parser):
        mock_os_path_exists.return_value = True
        expected = 'dict-of-profiles'
        mock_config_object = mock.Mock()
        mock_config_read = mock.Mock()
        mock_config_object.read = mock_config_read
        mock_config_parser.return_value = mock_config_object
        mock_config_object._sections = expected

        sections = awsumepy.get_profiles_from_ini_file('./path')
        self.assertEqual(sections, expected)

        mock_os_path_exists.return_value = False
        with self.assertRaises(SystemExit):
            awsumepy.get_profiles_from_ini_file('./path')

class TestGetINIProfileByName(unittest.TestCase):
    def test_get_ini_profile_by_name(self):
        user1 = collections.OrderedDict([('__name__', 'name1'), ('key', 'value')])
        user2 = collections.OrderedDict([('__name__', 'name1'), ('key', 'value')])
        user3 = collections.OrderedDict([('__name__', 'name1'), ('key', 'value')])

        sections = collections.OrderedDict()
        sections['user1'] = user1
        sections['user2'] = user2
        sections['user3'] = user3

        getUser1 = awsumepy.get_ini_profile_by_name('user1', sections)
        getUser2 = awsumepy.get_ini_profile_by_name('user2', sections)
        getUser3 = awsumepy.get_ini_profile_by_name('user3', sections)
        noUser = awsumepy.get_ini_profile_by_name('no_user', sections)

        self.assertEqual(user1, getUser1)
        self.assertEqual(user2, getUser2)
        self.assertEqual(user3, getUser3)
        self.assertEqual(noUser, collections.OrderedDict())

class TestGetConfigProfile(unittest.TestCase):
    @mock.patch('awsume.awsumepy.get_profiles_from_ini_file')
    @mock.patch('awsume.awsumepy.get_ini_profile_by_name')
    def test_get_config_profile(self, mock_get_ini_profile, mock_get_profiles):
        defaultArgs = argparse.Namespace()
        defaultArgs.default = True
        nonDefaultArgs = argparse.Namespace()
        nonDefaultArgs.default = False
        nonDefaultArgs.profile_name = 'name'

        mock_get_profiles.return_value = 'profiles'

        awsumepy.get_config_profile(defaultArgs)
        mock_get_ini_profile.assert_called_with('default', 'profiles')
        awsumepy.get_config_profile(nonDefaultArgs)
        mock_get_ini_profile.assert_called_with('profile name', 'profiles')

class TestGetCredentialsProfile(unittest.TestCase):
    @mock.patch('awsume.awsumepy.get_source_profile_from_role')
    @mock.patch('awsume.awsumepy.get_profiles_from_ini_file')
    @mock.patch('awsume.awsumepy.get_ini_profile_by_name')
    @mock.patch('awsume.awsumepy.is_role_profile')
    def test_get_credentials_profile(self,
                                     mock_is_role_profile,
                                     mock_get_ini_profile,
                                     mock_get_profiles,
                                     mock_get_source_profile):

        args = argparse.Namespace()
        args.profile_name = 'profile-name'

        mock_is_role_profile.return_value = True
        awsumepy.get_credentials_profile(collections.OrderedDict(), args)
        self.assertEqual(mock_get_source_profile.call_count, 1)

        mock_is_role_profile.return_value = False
        awsumepy.get_credentials_profile(collections.OrderedDict(), args)
        self.assertEqual(mock_get_ini_profile.call_count, 1)
        self.assertEqual(mock_get_profiles.call_count, 1)

class TestValidateProfiles(unittest.TestCase):
    @mock.patch('awsume.awsumepy.validate_credentials_profile')
    def test_validate_credentials(self, mock_validate_credentials):
        config = None
        credentials = None
        with self.assertRaises(SystemExit):
            awsumepy.validate_profiles(config, credentials)

        config = 'something'
        credentials = 'something'
        awsumepy.validate_profiles(config, credentials)
        self.assertEqual(mock_validate_credentials.call_count, 1)

class TestHandleProfiles(unittest.TestCase):
    @mock.patch('awsume.awsumepy.requires_mfa')
    @mock.patch('awsume.awsumepy.is_role_profile')
    @mock.patch('awsume.awsumepy.validate_profiles')
    def test_handle_profiles(self,
                             mock_validate_profiles,
                             mock_is_role_profile,
                             mock_requires_mfa):
        config = collections.OrderedDict()
        credentials = collections.OrderedDict()

        mock_requires_mfa.return_value = False
        mock_is_role_profile.return_value = False
        capturedOut = StringIO.StringIO()
        sys.stdout = capturedOut
        with self.assertRaises(SystemExit):
            awsumepy.handle_profiles(config, credentials)
        sys.stdout = sys.__stdout__
        self.assertTrue('Awsume' in capturedOut.getvalue())

        mock_is_role_profile.return_value = True
        awsumepy.handle_profiles(config, credentials)

        mock_requires_mfa.return_value = True
        mock_is_role_profile.return_value = False
        awsumepy.handle_profiles(config, credentials)

        mock_is_role_profile.return_value = True
        awsumepy.handle_profiles(config, credentials)

        self.assertEqual(mock_validate_profiles.call_count, 4)

class TestRequiresMFA(unittest.TestCase):
    def test_requires_mfa(self):
        configWithMFA = collections.OrderedDict()
        configWithMFA['mfa_serial'] = 'some_mfa_serial'
        configWithoutMFA = collections.OrderedDict()

        self.assertTrue(awsumepy.requires_mfa(configWithMFA))
        self.assertFalse(awsumepy.requires_mfa(configWithoutMFA))

class TestGetUserCredentials(unittest.TestCase):
    @mock.patch('awsume.awsumepy.create_boto_sts_client')
    @mock.patch('awsume.awsumepy.write_awsume_session_to_file')
    @mock.patch('awsume.awsumepy.create_awsume_session')
    @mock.patch('awsume.awsumepy.get_session_token_credentials')
    @mock.patch('awsume.awsumepy.is_valid_awsume_session')
    @mock.patch('awsume.awsumepy.read_awsume_session_from_file')
    def test_get_user_credentials(self,
                                  mock_read_session,
                                  mock_valid_session,
                                  mock_get_session_token,
                                  mock_create_awsume_session,
                                  mock_write_awsume_session,
                                  mock_create_sts_client):
        config = collections.OrderedDict()
        credentials = collections.OrderedDict()
        credentials['__name__'] = 'credentials-name'
        args = argparse.Namespace()

        args.refresh = False
        mock_valid_session.return_value = True
        awsumepy.get_user_credentials(config, credentials, args)
        self.assertEqual(mock_create_sts_client.call_count, 0)
        self.assertEqual(mock_get_session_token.call_count, 0)
        self.assertEqual(mock_create_awsume_session.call_count, 0)
        self.assertEqual(mock_write_awsume_session.call_count, 0)

        args.refresh = False
        mock_valid_session.return_value = False
        awsumepy.get_user_credentials(config, credentials, args)
        self.assertEqual(mock_create_sts_client.call_count, 1)
        self.assertEqual(mock_get_session_token.call_count, 1)
        self.assertEqual(mock_create_awsume_session.call_count, 1)
        self.assertEqual(mock_write_awsume_session.call_count, 1)

        args.refresh = True
        mock_valid_session.return_value = True
        awsumepy.get_user_credentials(config, credentials, args)
        self.assertEqual(mock_create_sts_client.call_count, 2)
        self.assertEqual(mock_get_session_token.call_count, 2)
        self.assertEqual(mock_create_awsume_session.call_count, 2)
        self.assertEqual(mock_write_awsume_session.call_count, 2)

        args.refresh = True
        mock_valid_session.return_value = False
        awsumepy.get_user_credentials(config, credentials, args)
        self.assertEqual(mock_create_sts_client.call_count, 3)
        self.assertEqual(mock_get_session_token.call_count, 3)
        self.assertEqual(mock_create_awsume_session.call_count, 3)
        self.assertEqual(mock_write_awsume_session.call_count, 3)

        self.assertEqual(mock_read_session.call_count, 4)

class TestGetRoleCredentials(unittest.TestCase):
    @mock.patch('awsume.awsumepy.create_boto_sts_client')
    @mock.patch('awsume.awsumepy.get_assume_role_credentials')
    @mock.patch('awsume.awsumepy.create_awsume_session')
    def test_get_role_credentials(self,
                                  mock_create_session,
                                  mock_get_role_credentials,
                                  mock_create_sts_client):

        mock_create_sts_client.return_value = 'the-role-client'

        config = collections.OrderedDict()
        config['__name__'] = 'profile the-name'
        config['role_arn'] = 'the-role-arn'
        userSession = collections.OrderedDict()
        userSession['SecretAccessKey'] = 'the-secret-access-key'
        userSession['AccessKeyId'] = 'the-access-key-id'
        userSession['SessionToken'] = 'the-session-token'

        awsumepy.get_role_credentials(config, userSession)
        self.assertEqual(mock_create_session.call_count, 1)
        self.assertEqual(mock_get_role_credentials.call_count, 1)
        mock_get_role_credentials.assert_called_with('the-role-client', 'the-role-arn', 'the-name-awsume-session')
        self.assertEqual(mock_create_sts_client.call_count, 1)

class TestStartAutoRefresher(unittest.TestCase):
    @mock.patch('awsume.awsumepy.kill_all_auto_processes')
    @mock.patch('awsume.awsumepy.write_auto_awsume_session')
    def test_start_auto_refresher(self, mock_write_auto_session, mock_kill_all):
        capturedOut = StringIO.StringIO()
        sys.stdout = capturedOut

        args = argparse.Namespace()
        args.profile_name = 'profile-name'
        userSession = collections.OrderedDict()
        config = collections.OrderedDict()
        config['role_arn'] = 'the-role-arn'
        credentials = collections.OrderedDict()
        credentials['__name__'] = 'creds-name'

        with self.assertRaises(SystemExit):
            awsumepy.start_auto_refresher(args, userSession, config, credentials)

        sys.stdout = sys.__stdout__
        self.assertTrue('Auto' in capturedOut.getvalue())

class TestHandleGettingRoleCredentials(unittest.TestCase):
    @mock.patch('awsume.awsumepy.is_role_profile')
    @mock.patch('awsume.awsumepy.get_role_credentials')
    @mock.patch('awsume.awsumepy.start_auto_refresher')
    def test_handle_getting_role_credentials(self,
                                             mock_start_auto,
                                             mock_get_role,
                                             mock_is_role):
        config = collections.OrderedDict()
        credentials = collections.OrderedDict()
        userSession = collections.OrderedDict()
        args = argparse.Namespace()

        mock_is_role.return_value = True
        args.auto_refresh = True
        awsumepy.handle_getting_role_credentials(config, credentials, userSession, args)
        self.assertEqual(mock_start_auto.call_count, 1)
        self.assertEqual(mock_get_role.call_count, 0)
        args.auto_refresh = False
        awsumepy.handle_getting_role_credentials(config, credentials, userSession, args)
        mock_get_role.assert_called_with(config, userSession)

        mock_is_role.return_value = False
        args.auto_refresh = True
        self.assertIsNone(awsumepy.handle_getting_role_credentials(config, credentials, userSession, args))
        args.auto_refresh = False
        self.assertIsNone(awsumepy.handle_getting_role_credentials(config, credentials, userSession, args))

class TestValidateCredentialsProfile(unittest.TestCase):
    def test_validate_credentials_profile(self):
        credentials = collections.OrderedDict()
        with self.assertRaises(SystemExit):
            awsumepy.validate_credentials_profile(credentials)

        credentials['aws_access_key_id'] = 'the-access-key-id'
        with self.assertRaises(SystemExit):
            awsumepy.validate_credentials_profile(credentials)

        del credentials['aws_access_key_id']
        credentials['aws_secret_access_key'] = 'the-secret-access-key'
        with self.assertRaises(SystemExit):
            awsumepy.validate_credentials_profile(credentials)

        credentials['aws_access_key_id'] = 'the-access-key-id'
        awsumepy.validate_credentials_profile(credentials)

class TestGetSourceProfileFromRole(unittest.TestCase):
    @mock.patch('awsume.awsumepy.get_profiles_from_ini_file')
    @mock.patch('awsume.awsumepy.get_ini_profile_by_name')
    @mock.patch('awsume.awsumepy.is_role_profile')
    @mock.patch('os.path.exists')
    def test_get_source_profile_from_role(self,
                                          mock_os_path_exists,
                                          mock_is_role_profile,
                                          mock_get_ini_profile,
                                          mock_get_profiles):

        config = collections.OrderedDict()
        config['source_profile'] = 'the-source'
        path = './path'
        expected = collections.OrderedDict()
        expected['some_key'] = 'some_value'

        mock_os_path_exists.return_value = True
        mock_is_role_profile.return_value = True
        mock_get_ini_profile.return_value = collections.OrderedDict()
        with self.assertRaises(SystemExit):
            awsumepy.get_source_profile_from_role(config, path)
        mock_get_ini_profile.return_value = expected
        self.assertEqual(awsumepy.get_source_profile_from_role(config, path), expected)
        mock_is_role_profile.return_value = False
        self.assertEqual(awsumepy.get_source_profile_from_role(config, path), collections.OrderedDict())
        mock_os_path_exists.return_value = False
        with self.assertRaises(SystemExit):
            awsumepy.get_source_profile_from_role(config, path)

class TestIsRoleProfile(unittest.TestCase):
    def test_is_role_profile(self):
        roleProfile = collections.OrderedDict()
        roleProfile['source_profile'] = 'the-source'
        roleProfile['role_arn'] = 'the-role-arn'
        brokenRole1 = collections.OrderedDict()
        brokenRole1['source_profile'] = 'the-source'
        brokenRole2 = collections.OrderedDict()
        brokenRole2['role_arn'] = 'the-role-arn'
        nonRole = collections.OrderedDict()

        self.assertTrue(awsumepy.is_role_profile(roleProfile))
        self.assertFalse(awsumepy.is_role_profile(nonRole))
        with self.assertRaises(SystemExit):
            awsumepy.is_role_profile(brokenRole1)
        with self.assertRaises(SystemExit):
            awsumepy.is_role_profile(brokenRole2)

class TestReadMFA(unittest.TestCase):
    @mock.patch('__builtin__.raw_input')
    def test_read_mfa(self, mock_input):
        mock_input.return_value = 'input'
        self.assertEqual(awsumepy.read_mfa(), 'input')

class TestIsValidMFA(unittest.TestCase):
    def test_is_valid_mfa(self):
        #for i in range(0, 1000000):
            #self.assertTrue(awsumepy.is_valid_mfa_token(str(i).rjust(6, '0')))
        self.assertFalse(awsumepy.is_valid_mfa_token('abcdef'))
        self.assertFalse(awsumepy.is_valid_mfa_token('12345a'))
        self.assertFalse(awsumepy.is_valid_mfa_token('!@#$%^'))
        self.assertFalse(awsumepy.is_valid_mfa_token('12345'))
        self.assertFalse(awsumepy.is_valid_mfa_token('1234567'))

class TestCreateBotoSTSClient(unittest.TestCase):
    @mock.patch('boto3.Session')
    def test_create_boto_sts_client(self,
                                    mock_boto_session_function):
        mock_boto_client = mock.Mock()
        mock_returned_session = mock.Mock()
        mock_returned_session.client = mock_boto_client
        mock_boto_session_function.return_value = mock_returned_session
        awsumepy.create_boto_sts_client('profile-name',
                                        'secret-access-key',
                                        'access-key-id',
                                        'session-token')
        self.assertEqual(mock_boto_session_function.call_count, 1)
        self.assertEqual(mock_boto_client.call_count, 1)

class TestGetSessionTokenCredentials(unittest.TestCase):
    @mock.patch('awsume.awsumepy.is_valid_mfa_token')
    @mock.patch('awsume.awsumepy.read_mfa')
    def test_get_session_token_credentials(self,
                                           mock_read_mfa,
                                           mock_valid_mfa):
        profile = collections.OrderedDict()
        mock_get_session_token = mock.Mock()
        mock_get_session_token.return_value = 'session-token'
        mock_token_client = mock.Mock()
        mock_token_client.get_session_token = mock_get_session_token
        mock_read_mfa.return_value = '000000'

        self.assertEqual(awsumepy.get_session_token_credentials(mock_token_client, profile), 'session-token')
        profile['mfa_serial'] = 'some-mfa-serial'
        self.assertEqual(awsumepy.get_session_token_credentials(mock_token_client, profile), 'session-token')
        mock_get_session_token.assert_called_with(SerialNumber='some-mfa-serial', TokenCode='000000')
        mock_get_session_token.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            awsumepy.get_session_token_credentials(mock_token_client, profile)

class TestGetAssumeRoleCredentials(unittest.TestCase):
    def test_get_assume_role_credentials(self):
        roleArn = 'role-arn'
        roleSessionName = 'role-session-name'
        mock_assume_role_client = mock.Mock()
        mock_assume_role_function = mock.Mock()
        mock_assume_role_client.assume_role = mock_assume_role_function

        awsumepy.get_assume_role_credentials(mock_assume_role_client, roleArn, roleSessionName)
        mock_assume_role_function.assert_called_once_with(RoleArn='role-arn', RoleSessionName='role-session-name')

        mock_assume_role_function.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            awsumepy.get_assume_role_credentials(mock_assume_role_client, roleArn, roleSessionName)

class TestCreateAwsumeSession(unittest.TestCase):
    @mock.patch('datetime.datetime')
    def test_create_awsume_session(self, mock_datetime):
        mock_astimezone = mock.Mock()
        mock_astimezone.return_value = datetime.datetime.min
        mock_datetime.astimezone = mock_astimezone

        credentials = collections.OrderedDict()
        config = collections.OrderedDict()

        with self.assertRaises(SystemExit):
            awsumepy.create_awsume_session(credentials, config)

        credentials['Credentials'] = collections.OrderedDict()
        credentials['Credentials']['SecretAccessKey'] = 'secret-access-key'
        credentials['Credentials']['SessionToken'] = 'session-token'
        credentials['Credentials']['AccessKeyId'] = 'access-key-id'
        config['region'] = 'region'
        expected = copy.copy(credentials['Credentials'])
        expected['region'] = 'region'
        expected['Expiration'] = None

        self.assertEqual(awsumepy.create_awsume_session(credentials, config), expected)

        credentials['Credentials']['Expiration'] = datetime.datetime.max
        awsumepy.create_awsume_session(credentials, config)

class TestSessionString(unittest.TestCase):
    def test_session_string(self):
        session = collections.OrderedDict()
        session['SecretAccessKey'] = 'secret-access-key'
        session['SessionToken'] = 'session-token'
        session['AccessKeyId'] = 'access-key-id'
        session['region'] = 'region'
        expected = 'secret-access-key session-token access-key-id region'
        self.assertEqual(awsumepy.session_string(session), expected)

class TestParseSessionString(unittest.TestCase):
    @mock.patch('datetime.datetime')
    def test_parse_session_string(self, mock_datetime):
        mock_strptime = mock.Mock()
        mock_strptime.return_value = 'expiration'
        mock_datetime.strptime = mock_strptime
        string = 'secret-access-key session-token access-key-id region expiration'
        expected = collections.OrderedDict()
        expected['SecretAccessKey'] = 'secret-access-key'
        expected['SessionToken'] = 'session-token'
        expected['AccessKeyId'] = 'access-key-id'
        expected['region'] = 'region'
        expected['Expiration'] = 'expiration'
        self.assertEqual(awsumepy.parse_session_string(string), expected)

class TestWriteAwsumeSessionToFile(unittest.TestCase):
    @mock.patch('datetime.datetime')
    @mock.patch('__builtin__.open')
    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_write_awsume_session_to_file(self,
                                          mock_os_path_exists,
                                          mock_os_mkdirs,
                                          mock_open,
                                          mock_datetime):
        mock_strftime = mock.Mock()
        mock_strftime.return_value = 'expiration'
        mock_datetime.strftime = mock_strftime
        mock_file = mock.Mock()
        mock_file.write = mock.Mock()
        mock_file.close = mock.Mock()
        mock_open.return_value = mock_file

        path = './path'
        filename = 'file-name'
        session = collections.OrderedDict()

        mock_os_path_exists.return_value = False
        awsumepy.write_awsume_session_to_file(path, filename, session)
        mock_os_mkdirs.assert_called_once_with(path)
        self.assertEqual(mock_file.write.call_count, 1)
        self.assertEqual(mock_file.close.call_count, 1)

        session['Expiration'] = datetime.datetime.min

        mock_os_path_exists.return_value = True
        awsumepy.write_awsume_session_to_file(path, filename, session)
        self.assertEqual(mock_file.write.call_count, 2)
        self.assertEqual(mock_file.close.call_count, 2)

class TestReadAwsumeSessionFromFile(unittest.TestCase):
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('awsume.awsumepy.parse_session_string')
    def test_read_awsume_session_from_file(self,
                                           mock_parse_session_string,
                                           mock_os_path_isfile,
                                           mock_open):
        mock_file = mock.Mock()
        mock_file.read = mock.Mock()
        mock_open.return_value = mock_file
        mock_parse_session_string.return_value = 'awsume-session'
        path = './path'
        name = 'name'

        mock_os_path_isfile.return_value = False
        self.assertEqual(awsumepy.read_awsume_session_from_file(path, name), collections.OrderedDict())

        mock_os_path_isfile.return_value = True
        self.assertEqual(awsumepy.read_awsume_session_from_file(path, name), 'awsume-session')

class TestIsValidAwsumeSession(unittest.TestCase):
    def test_is_valid_awsume_session(self):
        session = collections.OrderedDict()

        self.assertFalse(awsumepy.is_valid_awsume_session(session))

        session['Expiration'] = datetime.datetime.min
        self.assertFalse(awsumepy.is_valid_awsume_session(session))

        session['Expiration'] = datetime.datetime.max
        self.assertTrue(awsumepy.is_valid_awsume_session(session))

class TestWriteAutoAwsumeSession(unittest.TestCase):
    @mock.patch('ConfigParser.ConfigParser')
    def test_write_auto_awsume_session(self,
                                       mock_config_parser):
        mock_parser = mock.Mock()
        mock_parser_write = mock.Mock()
        mock_parser_read = mock.Mock()
        mock_parser_has_section = mock.Mock()
        mock_parser_remove_section = mock.Mock()

        mock_parser.write = mock_parser_write
        mock_parser.read = mock_parser_read
        mock_parser.has_section = mock_parser_has_section
        mock_parser.remove_section = mock_parser_remove_section

        mock_config_parser.return_value = mock_parser

        name = 'name'
        file = './path'
        roleArn = 'role-arn'
        session = collections.OrderedDict()
        session['SessionToken'] = 'session-token'
        session['AccessKeyId'] = 'access-key-id'
        session['SecretAccessKey'] = 'secret-access-key'
        session['region'] = 'region'

        mock_parser_has_section.return_value = True
        awsumepy.write_auto_awsume_session(name, session, file, roleArn)
        mock_parser_remove_section.assert_called_with(name)

        mock_parser_has_section.return_value = False
        awsumepy.write_auto_awsume_session(name, session, file, roleArn)
        self.assertEqual(mock_parser_write.call_count, 2)

class TestKillAllAutoProcesses(unittest.TestCase):
    @mock.patch('psutil.process_iter')
    def test_kill_all_auto_processes(self,
                                     mock_process_iter):
        mock_auto_proc = mock.Mock()
        mock_norm_proc = mock.Mock()

        mock_process_iter.return_value = [mock_auto_proc, mock_norm_proc]

        mock_auto_proc_cmdline = mock.Mock()
        mock_auto_kill = mock.Mock()
        mock_auto_proc_cmdline.return_value = ['autoAwsume', 'other-cmdline-options']
        mock_auto_proc.cmdline = mock_auto_proc_cmdline
        mock_auto_proc.kill = mock_auto_kill

        mock_norm_proc_cmdline = mock.Mock()
        mock_norm_kill = mock.Mock()
        mock_norm_proc_cmdline.return_value = ['normal', 'process-command']
        mock_norm_proc.cmdline = mock_norm_proc_cmdline
        mock_norm_proc.kill = mock_norm_kill

        awsumepy.kill_all_auto_processes()

        self.assertEqual(mock_auto_kill.call_count, 1)
        self.assertEqual(mock_norm_kill.call_count, 0)

class TestRemoveAllAutoProfiles(unittest.TestCase):
    @mock.patch('__builtin__.open')
    @mock.patch('ConfigParser.ConfigParser')
    def test_remove_all_auto_profiles(self,
                                      mock_config_parser,
                                      mock_open):
        profiles = collections.OrderedDict([('auto-refresh-profile', collections.OrderedDict([('__name__', 'auto-refresh-profile'), ('region', 'us-east-1')]))])

        mock_parser_object = mock.Mock()
        mock_parser_read = mock.Mock()
        mock_parser_write = mock.Mock()
        mock_parser_remove = mock.Mock()
        mock_parser_object.read = mock_parser_read
        mock_parser_object.write = mock_parser_write
        mock_parser_object.remove_section = mock_parser_remove
        mock_parser_object._sections = profiles
        mock_config_parser.return_value = mock_parser_object

        awsumepy.remove_all_auto_profiles('./path')
        mock_parser_remove.assert_called_once_with('auto-refresh-profile')

class TestRemoveAutoAwsumeProfileByName(unittest.TestCase):
    @mock.patch('__builtin__.open')
    @mock.patch('ConfigParser.ConfigParser')
    def test_remove_auto_awsume_profile_by_name(self,
                                                mock_config_parser,
                                                mock_open):
        profiles = collections.OrderedDict([('auto-refresh-profileToRemove', collections.OrderedDict([('__name__', 'auto-refresh-profile'), ('region', 'us-east-1')])), ('auto-refresh-profile', collections.OrderedDict([('__name__', 'auto-refresh-profile'), ('region', 'us-east-1')]))])

        mock_parser_object = mock.Mock()
        mock_parser_read = mock.Mock()
        mock_parser_write = mock.Mock()
        mock_parser_remove = mock.Mock()
        mock_parser_object.read = mock_parser_read
        mock_parser_object.write = mock_parser_write
        mock_parser_object.remove_section = mock_parser_remove
        mock_parser_object._sections = profiles
        mock_config_parser.return_value = mock_parser_object

        awsumepy.remove_auto_awsume_profile_by_name('profileToRemove', './path')
        mock_parser_remove.assert_called_once_with('auto-refresh-profileToRemove')
        self.assertTrue('auto-refresh-profileToStay' not in mock_parser_remove.call_args_list)

class TestIsAutoRefreshProfiles(unittest.TestCase):
    @mock.patch('ConfigParser.ConfigParser')
    def test_is_auto_refresh_profiles(self,
                                      mock_config_parser):
        mock_parser_object = mock.Mock()
        mock_config_parser.return_value = mock_parser_object

        list_with_auto = ['some-profile', 'auto-refresh-profile', 'some-other-profile']
        list_no_auto = ['some-profile', 'some-other-profile']

        mock_parser_object._sections = list_with_auto
        self.assertTrue(awsumepy.is_auto_refresh_profiles('./path'))

        mock_parser_object._sections = list_no_auto
        self.assertFalse(awsumepy.is_auto_refresh_profiles('./path'))

class TestStopAutoRefresh(unittest.TestCase):
    @mock.patch('awsume.awsumepy.kill_all_auto_processes')
    @mock.patch('awsume.awsumepy.is_auto_refresh_profiles')
    @mock.patch('awsume.awsumepy.remove_auto_awsume_profile_by_name')
    @mock.patch('awsume.awsumepy.remove_all_auto_profiles')
    def test_stop_auto_refresh(self,
                               mock_remove_all_auto_profiles,
                               mock_remove_auto_profile_by_name,
                               mock_is_auto_refresh_profiles,
                               mock_kill_all_auto_processes):

        mock_is_auto_refresh_profiles.return_value = False

        with self.assertRaises(SystemExit):
            awsumepy.stop_auto_refresh()
        self.assertEqual(mock_remove_all_auto_profiles.call_count, 1)
        self.assertEqual(mock_remove_auto_profile_by_name.call_count, 0)

        with self.assertRaises(SystemExit):
            awsumepy.stop_auto_refresh('some-profile')
        self.assertEqual(mock_remove_all_auto_profiles.call_count, 1)
        self.assertEqual(mock_remove_auto_profile_by_name.call_count, 1)

        capturedOut = StringIO.StringIO()
        sys.stdout = capturedOut
        with self.assertRaises(SystemExit):
            awsumepy.stop_auto_refresh('some-profile')
        sys.stdout = sys.__stdout__
        self.assertTrue('Kill' in capturedOut.getvalue())
        self.assertEqual(mock_kill_all_auto_processes.call_count, 3)

        mock_is_auto_refresh_profiles.return_value = True
        capturedOut = StringIO.StringIO()
        sys.stdout = capturedOut
        with self.assertRaises(SystemExit):
            awsumepy.stop_auto_refresh('some-profile')
        sys.stdout = sys.__stdout__
        self.assertTrue('Stop' in capturedOut.getvalue())
        self.assertEqual(mock_kill_all_auto_processes.call_count, 3)

class TestGenerateFormattedData(unittest.TestCase):
    def test_generate_formatted_data(self):
        pass

class TestPrintFormattedData(unittest.TestCase):
    def test_print_formatted_data(self):
        capturedOut = StringIO.StringIO()
        sys.stderr = capturedOut
        awsumepy.print_formatted_data('some-formatted-data')
        sys.stderr = sys.__stderr__
        self.assertNotEqual(capturedOut.getvalue(), '')

class TestListProfileData(unittest.TestCase):
    @mock.patch('awsume.awsumepy.print_formatted_data')
    @mock.patch('awsume.awsumepy.generate_formatted_data')
    @mock.patch('awsume.awsumepy.get_profiles_from_ini_file')
    def test_list_profile_data(self,
                               mock_get_profiles,
                               mock_generate_data,
                               mock_print_data):
        awsumepy.list_profile_data('./path', './path')
        self.assertEqual(mock_get_profiles.call_count, 2)
        self.assertEqual(mock_generate_data.call_count, 1)
        self.assertEqual(mock_print_data.call_count, 1)


if __name__ == '__main__':
    unittest.main()
