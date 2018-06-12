"use strict";

var gulp = require('gulp');

// ** UTILITY PLUGINS ** //
var concat = require('gulp-concat');
var rename = require('gulp-rename');
var del = require('del');
var filter = require('gulp-filter');
var watch = require('gulp-watch');
var debug = require('gulp-debug');
var gulpif = require('gulp-if');
var rsync = require('gulp-rsync');
var argv = require('yargs').argv;
var po2json = require('gulp-po2json');
var mainBowerFiles = require('main-bower-files');
var wait = require('gulp-wait')

// ** SASS/SCSS/CSS PLUGINS ** //
var sass = require('gulp-sass');

// ** JAVASCRIPT PLUGINS ** //
var uglify = require('gulp-uglify');
var jshint = require('gulp-jshint');
var sourcemaps = require('gulp-sourcemaps');

// ** IMAGE OPTIMISATION PLUGINS ** //
var imagemin = require('gulp-imagemin');
var pngquant = require('imagemin-pngquant');
var optipng = require('imagemin-optipng');
var jpegoptim = require('imagemin-jpegoptim');

// ** SETTINGS ** //
// To build production site, run: gulp --production
var production = !!(argv.production);

// JAVASCRIPT TASKS
gulp.task('jshint', function() {
    return gulp.src('meerkat_auth/src/js/**/*.js')
        .pipe(jshint())
        .pipe(jshint.reporter('default'))
        .pipe(jshint.reporter("fail"));
});

gulp.task('vendorJS', function() {
	return gulp.src( mainBowerFiles().concat([]))
        .pipe(filter('*.js'))
        .pipe(gulpif(production, uglify()))
        .pipe(gulp.dest('meerkat_auth/static/js'));
});

gulp.task('appJS', function() {
    return gulp.src(['meerkat_auth/src/js/**/*.js'])
        .pipe(concat('app.js'))
        .pipe(gulpif(production, uglify()))
        .pipe(gulp.dest('meerkat_auth/static/js'));
});

gulp.task('js', gulp.parallel('vendorJS', gulp.series('jshint', 'appJS')));

// SASS/CSS TASKS
gulp.task('rename-css-to-scss', function() {
    return gulp.src(mainBowerFiles())
        .pipe(filter('*.css'))
        .pipe(rename(function(path) {path.extname = ".scss"}))
        .pipe(gulp.dest('meerkat_auth/src/sass/autogenerated'));
});

gulp.task('sass', function() {
    return gulp.src('meerkat_auth/src/sass/main.scss')
        .pipe(gulpif(
            production,
            sass({outputStyle: 'compressed'}).on('error', sass.logError),
            sass({outputStyle: 'expanded'}).on('error', sass.logError)
        )).pipe(gulp.dest('meerkat_auth/static/css'));
});

gulp.task('styles', gulp.series('rename-css-to-scss', 'sass'));

gulp.task('vendor-css', function(){
  return gulp.src(mainBowerFiles())
    .pipe( filter('*.css') )
    .pipe(gulp.dest('meerkat_auth/static/css/'));
});

// FONT TASKS
gulp.task('fonts', function() {
  return gulp.src([
      'bower_components/fontawesome/fonts/*',
      'bower_components/bootstrap-sass/assets/fonts/bootstrap/*'
    ])
    .pipe(gulp.dest('meerkat_auth/static/fonts'));
});

// IMG TASKS
gulp.task('img', function() {
return gulp.src(['meerkat_auth/src/img/**/*.{jpg,png,svg,gif}'])
    .pipe(imagemin({
        optimizationLevel: 3,
        progressive: true,
        svgoPlugins: [{removeViewBox: false}],
        use: [
            pngquant(),
            optipng({optimizationLevel: 3}),
            jpegoptim({max: 50, progressive: true}),
        ]
    }))
    .pipe(gulp.dest('meerkat_auth/static/img/'));
});

//LANGUAGE TASKS
gulp.task('po2json', function () {
    return gulp.src(['meerkat_auth/translations/*/LC_MESSAGES/messages.po'])
		.pipe(debug())
        .pipe(po2json({format:"jed1.x"}))
        .pipe(gulp.dest('meerkat_auth/static/translations'));
});

gulp.task('locales', function() {
	return gulp.src(['bower_components/moment/locale/fr.js'])
        .pipe(filter('*.js'))
        .pipe(gulpif(production, uglify()))
        .pipe(gulp.dest('meerkat_auth/static/js/locale'));
});

// CLEAN TASKS
gulp.task('clean', function(done){
    del([
        'meerkat_auth/src/sass/autogenerated/**/*',
        'meerkat_auth/static/css/**/*',
        'meerkat_auth/static/js/**/*',
        'meerkat_auth/static/js/locale/**',
        'meerkat_auth/static/fonts/**/*',
        'meerkat_auth/static/img/**/*.{gif,jpg,png,svg}',
        'meerkat_auth/static/translations/**/*.json'
    ]);
    done();
});

// DEFAULT TASK , 'fonts', 'img', 'files', 'vendor-css', 'po2json', 'locales'
gulp.task('default', gulp.series('clean', gulp.parallel(
    'styles', 'js', 'fonts', 'img', 'vendor-css', 'po2json', 'locales'
)));
